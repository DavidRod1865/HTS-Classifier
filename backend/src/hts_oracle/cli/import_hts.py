"""
CSV → Postgres + Embeddings import script.

Usage:
    python -m hts_oracle.cli.import_hts data/hts_2026_revision_4_enriched.csv

What it does:
    1. Reads the CSV file
    2. Filters to leaf nodes only (non-leaves are category headers, not searchable)
    3. For each leaf node, builds the text to embed
    4. Calls OpenAI in batches of 100 to generate embeddings
    5. Upserts rows into the hts_codes table (safe to re-run)

The script prints progress as it goes so you can watch it work.
"""

import asyncio
import csv
import sys
import time
from pathlib import Path

from openai import AsyncOpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from hts_oracle.config import get_settings
from hts_oracle.models import HtsCode


# ---------------------------------------------------------------------------
# Text building — what gets embedded as a vector
# ---------------------------------------------------------------------------
# This is one of the most important functions in the whole system.
# The quality of the embedding text directly determines search accuracy.
#
# We prefer "Enriched Text" (AI-generated, detailed, includes synonyms
# and common ways people describe the product) over the raw description
# (which is often terse like "Of cotton" or "Males").

def build_embed_text(row: dict) -> str:
    """
    Build the text that gets turned into a vector embedding.

    Priority:
      1. Enriched Text + Context Path  (best quality — AI-generated synonyms)
      2. Enhanced Description + Search Keywords + Context Path  (fallback)

    The context path (e.g., "Apparel > Knitted > T-shirts") adds hierarchy
    information that helps disambiguate similar descriptions.
    """
    enriched = row.get("Enriched Text", "").strip()
    context_path = row.get("Context Path", "").strip()

    if enriched:
        # Enriched text already includes synonyms and detailed descriptions.
        # Adding the context path gives the embedding hierarchy awareness.
        # If context path is empty, just return enriched text.
        return f"{enriched}\n{context_path}" if context_path else enriched 

    # Fallback: combine what we have
    parts = [
        row.get("Enhanced Description", "").strip(),
        row.get("Search Keywords", "").strip(),
        context_path,
    ]
    return "\n".join(part for part in parts if part)
    # Note: If all fields are empty, this will return an empty string, which is valid but won't produce a useful embedding.


def clean_unit(raw_unit: str) -> str:
    """
    Clean up the unit field from the CSV.

    The CSV stores units as JSON arrays like '["No."]' or '["kg"]'.
    We strip the brackets to get a clean string like "No." or "kg".
    """
    if not raw_unit:
        return ""
    # Remove JSON array wrapping: ["No."] → No.
    return raw_unit.strip().strip("[]\"' ")


# ---------------------------------------------------------------------------
# Main import logic
# ---------------------------------------------------------------------------

async def import_csv(csv_path: str):
    """
    Read a CSV file and import all leaf-node HTS codes into Postgres.

    This function:
      1. Reads and filters the CSV
      2. Generates embeddings via OpenAI (batches of 200)
      3. Upserts each row into the hts_codes table
    """
    settings = get_settings()
    csv_file = Path(csv_path)

    if not csv_file.exists():
        print(f"ERROR: File not found: {csv_file}")
        sys.exit(1)

    # --- Step 1: Read CSV and filter to leaf nodes ---
    print(f"Reading {csv_file.name}...")

    with open(csv_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        # Only leaf nodes are actual classifiable products.
        # Non-leaf nodes are category headers (e.g., "Chapter 61: Knitted apparel")
        all_rows = [row for row in reader if row.get("Is Leaf Node") == "Yes"]

    print(f"Found {len(all_rows)} leaf-node HTS codes")

    # --- Step 2: Connect to database ---
    # CLI scripts create their own engine (not the app's global one)
    # statement_cache_size=0: required for Supabase/PgBouncer which doesn't
    # support prepared statements in transaction pooling mode
    engine = create_async_engine(
        settings.database_url,
        connect_args={"statement_cache_size": 0},
    )
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # --- Step 3: Generate embeddings and upsert in batches ---
    openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
    batch_size = 200
    total_imported = 0
    total_embedded = 0
    start_time = time.time()

    for batch_start in range(0, len(all_rows), batch_size):
        batch = all_rows[batch_start : batch_start + batch_size]
        batch_num = batch_start // batch_size + 1
        total_batches = (len(all_rows) + batch_size - 1) // batch_size

        print(f"\nBatch {batch_num}/{total_batches} ({len(batch)} codes)...")

        # Build the text to embed for each row in this batch
        texts_to_embed = [build_embed_text(row) for row in batch]

        # Call OpenAI to generate embeddings for all texts in one API call.
        embeddings = []
        try:
            response = await openai_client.embeddings.create(
                model=settings.embedding_model,
                input=texts_to_embed,
                dimensions=settings.embedding_dimensions,
            )
            embeddings = [item.embedding for item in response.data]
            total_embedded += len(embeddings)
            print(f"  ✓ Generated {len(embeddings)} embeddings")
        except Exception as e:
            print(f"  ✗ Embedding failed: {e}")
            print(f"    (importing rows without embeddings — re-run to retry)")
            embeddings = [None] * len(batch)

        # Upsert each row. Each batch commits independently, so if the
        # script crashes on batch 50, batches 1-49 are already saved.
        # Re-running skips those (upsert updates existing rows).
        try:
            async with session_factory() as session:
                for i, row in enumerate(batch):
                    hts_number = row.get("HTS Number", "").strip()
                    if not hts_number:
                        continue

                    # Check if this code already exists
                    existing = await session.execute(
                        select(HtsCode).where(HtsCode.hts_number == hts_number)
                    )
                    hts_code = existing.scalar_one_or_none()

                    if hts_code:
                        # Update existing row
                        hts_code.description = row.get("Original Description", "").strip()
                        hts_code.enhanced_description = row.get("Enhanced Description", "").strip()
                        hts_code.enriched_text = row.get("Enriched Text", "").strip()
                        hts_code.context_path = row.get("Context Path", "").strip()
                        hts_code.chapter = row.get("Category", "").strip()
                        hts_code.general_rate = row.get("General Rate of Duty", "").strip()
                        hts_code.special_rate = row.get("Special Rate of Duty", "").strip()
                        hts_code.unit = clean_unit(row.get("Unit of Quantity", ""))
                        hts_code.is_leaf = True
                        if embeddings[i] is not None:
                            hts_code.embedding = embeddings[i]
                    else:
                        # Insert new row
                        hts_code = HtsCode(
                            hts_number=hts_number,
                            description=row.get("Original Description", "").strip(),
                            enhanced_description=row.get("Enhanced Description", "").strip(),
                            enriched_text=row.get("Enriched Text", "").strip(),
                            context_path=row.get("Context Path", "").strip(),
                            chapter=row.get("Category", "").strip(),
                            general_rate=row.get("General Rate of Duty", "").strip(),
                            special_rate=row.get("Special Rate of Duty", "").strip(),
                            unit=clean_unit(row.get("Unit of Quantity", "")),
                            is_leaf=True,
                            embedding=embeddings[i] if embeddings[i] is not None else None,
                        )
                        session.add(hts_code)

                    total_imported += 1

                await session.commit()
                print(f"  ✓ Upserted {len(batch)} rows to database")
        except Exception as e:
            # If a batch fails (network hiccup, DB timeout), log it and continue.
            # The failed batch can be retried by re-running the script.
            print(f"  ✗ Database error on batch {batch_num}: {e}")
            print(f"    (re-run the script to retry failed batches)")

    # --- Summary ---
    elapsed = time.time() - start_time
    print(f"\n{'='*60}")
    print(f"Import complete!")
    print(f"  Rows imported:     {total_imported}")
    print(f"  Embeddings created: {total_embedded}")
    print(f"  Time elapsed:      {elapsed:.1f}s")
    print(f"{'='*60}")

    await engine.dispose()


# ---------------------------------------------------------------------------
# Entry point — run with: python -m hts_oracle.cli.import_hts <csv_path>
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) < 2:
        print("Usage: python -m hts_oracle.cli.import_hts <path-to-csv>")
        print("Example: python -m hts_oracle.cli.import_hts data/hts_2026_revision_4_enriched.csv")
        sys.exit(1)

    csv_path = sys.argv[1]
    asyncio.run(import_csv(csv_path))


if __name__ == "__main__":
    main()