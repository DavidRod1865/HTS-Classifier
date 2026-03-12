"""
Batch-enrich HTS descriptions with commercial product language using Claude Haiku.

Reads the source CSV, groups entries by chapter, sends batches to Claude for
enrichment, and writes a new CSV with an added "Enriched Text" column.

Resume-safe: tracks progress in .tmp/enrichment_progress.json so it can be
restarted without re-processing completed batches.

Usage:
    cd backend
    python src/enrich_descriptions.py                  # full run
    python src/enrich_descriptions.py --dry-run        # preview first batch only
    python src/enrich_descriptions.py --reset          # clear progress and start over
"""

import os
import sys
import csv
import json
import time
import logging
import argparse
from collections import defaultdict

from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger(__name__)

CLAUDE_MODEL = os.getenv("CLAUDE_MODEL_LIGHT", "claude-haiku-4-5-20251001")
BATCH_SIZE = 25  # entries per Claude call
MAX_RETRIES = 3

CSV_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "hts_2025_revision_13.csv"
)
OUTPUT_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "hts_2025_revision_13_enriched.csv"
)
TMP_DIR = os.path.join(os.path.dirname(__file__), "..", "..", ".tmp")
PROGRESS_PATH = os.path.join(TMP_DIR, "enrichment_progress.json")


def load_progress():
    """Load enrichment progress (completed batch keys and their results)."""
    if os.path.exists(PROGRESS_PATH):
        with open(PROGRESS_PATH, "r") as f:
            return json.load(f)
    return {"enriched": {}}  # hts_code → enriched_text


def save_progress(progress):
    os.makedirs(TMP_DIR, exist_ok=True)
    with open(PROGRESS_PATH, "w") as f:
        json.dump(progress, f)


def build_prompt(entries, chapter_context):
    """Build the enrichment prompt for a batch of HTS entries."""
    items = []
    for i, entry in enumerate(entries, 1):
        code = entry["HTS Number"].strip()
        desc = entry["Enhanced Description"].strip()
        path = entry.get("Context Path", "").strip()
        items.append(f"{i}. HTS {code}: {desc}" + (f" | Path: {path}" if path else ""))

    entries_text = "\n".join(items)

    return (
        "You are an HTS (Harmonized Tariff Schedule) expert who helps importers "
        "find the right tariff codes. For each leaf node below, write a rich "
        "commercial description that includes:\n"
        "- Common product names and brand-agnostic synonyms people would search for\n"
        "- Typical materials and forms\n"
        "- Common use cases and industries\n"
        "- Relevant specifications or dimensions people search by\n\n"
        "Keep each enrichment to 2-3 concise sentences. Focus on searchability — "
        "include the terms an importer or customs broker would actually type.\n\n"
        f"Chapter context: {chapter_context}\n\n"
        f"Entries:\n{entries_text}\n\n"
        "Respond with ONLY a JSON array, one object per entry, in order:\n"
        '[{"hts_code": "...", "enriched_text": "..."}, ...]'
    )


def parse_response(text, entries):
    """Parse Claude's JSON array, with fallbacks for each entry."""
    import re
    results = {}

    try:
        match = re.search(r"\[.*\]", text, re.DOTALL)
        parsed = json.loads(match.group() if match else text)
        if not isinstance(parsed, list):
            parsed = []
    except (json.JSONDecodeError, AttributeError):
        logger.warning("Failed to parse JSON response, using fallbacks")
        parsed = []

    for i, entry in enumerate(entries):
        code = entry["HTS Number"].strip()
        if i < len(parsed) and parsed[i].get("enriched_text", "").strip():
            results[code] = parsed[i]["enriched_text"].strip()
        else:
            # Fallback: use existing description + context path
            desc = entry["Enhanced Description"].strip()
            path = entry.get("Context Path", "").strip()
            results[code] = f"{desc} {path}".strip()

    return results


def enrich_batch(client, entries, chapter_context, dry_run=False):
    """Send one batch to Claude and return enriched texts."""
    prompt = build_prompt(entries, chapter_context)

    if dry_run:
        logger.info(f"[DRY RUN] Would send {len(entries)} entries to Claude")
        logger.info(f"Prompt preview:\n{prompt[:500]}...")
        return {e["HTS Number"].strip(): "[dry run placeholder]" for e in entries}

    for attempt in range(MAX_RETRIES):
        try:
            response = client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=200 * len(entries),
                messages=[{"role": "user", "content": prompt}],
            )
            return parse_response(response.content[0].text, entries)
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1} failed: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(2 ** attempt)
            else:
                logger.error(f"All retries failed for batch, using fallbacks")
                return {
                    e["HTS Number"].strip(): e["Enhanced Description"].strip()
                    for e in entries
                }


def run(dry_run=False, reset=False):
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: Set ANTHROPIC_API_KEY in your environment.", file=sys.stderr)
        sys.exit(1)

    client = Anthropic(api_key=api_key)

    # Load progress (or reset)
    if reset and os.path.exists(PROGRESS_PATH):
        os.remove(PROGRESS_PATH)
        logger.info("Progress reset.")
    progress = load_progress()
    enriched = progress["enriched"]

    # Load CSV
    logger.info(f"Loading {CSV_PATH}...")
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        all_rows = list(reader)

    leaf_nodes = [
        r for r in all_rows
        if (r.get("Is Leaf Node") or "").strip() == "Yes"
        and (r.get("HTS Number") or "").strip()
    ]
    logger.info(f"  {len(leaf_nodes)} leaf nodes to enrich")
    logger.info(f"  {len(enriched)} already enriched (from previous run)")

    # Group by chapter
    chapters = defaultdict(list)
    for row in leaf_nodes:
        code = row["HTS Number"].strip()
        chapter = code[:2] if len(code) >= 2 else "00"
        chapters[chapter].append(row)

    # Process each chapter in sub-batches
    total_processed = len(enriched)
    total_to_do = len(leaf_nodes)
    batch_count = 0

    for chapter in sorted(chapters.keys()):
        entries = chapters[chapter]
        # Get chapter context from the first entry's context path
        first_path = (entries[0].get("Context Path") or "").strip()
        chapter_context = first_path.split(" > ")[0] if first_path else f"Chapter {chapter}"

        for i in range(0, len(entries), BATCH_SIZE):
            batch = entries[i:i + BATCH_SIZE]

            # Skip entries already enriched
            unenriched = [e for e in batch if e["HTS Number"].strip() not in enriched]
            if not unenriched:
                continue

            batch_count += 1
            logger.info(
                f"Chapter {chapter} batch {i // BATCH_SIZE + 1} — "
                f"{len(unenriched)} entries ({total_processed}/{total_to_do} total)"
            )

            results = enrich_batch(client, unenriched, chapter_context, dry_run=dry_run)
            enriched.update(results)
            total_processed += len(results)

            # Save progress after each batch
            progress["enriched"] = enriched
            save_progress(progress)

            if dry_run:
                logger.info("Dry run — stopping after first batch.")
                return

            # Rate limiting: small pause between batches
            if batch_count % 10 == 0:
                time.sleep(1)

    logger.info(f"\nEnrichment complete. {len(enriched)} entries enriched.")

    # Write enriched CSV
    logger.info(f"Writing enriched CSV to {OUTPUT_PATH}...")
    output_fieldnames = list(fieldnames) + (["Enriched Text"] if "Enriched Text" not in fieldnames else [])

    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=output_fieldnames)
        writer.writeheader()
        for row in all_rows:
            code = (row.get("HTS Number") or "").strip()
            row["Enriched Text"] = enriched.get(code, "")
            writer.writerow(row)

    logger.info(f"Done. Enriched CSV written to {OUTPUT_PATH}")
    logger.info(f"Total batches processed: {batch_count}")


def main():
    parser = argparse.ArgumentParser(description="Enrich HTS descriptions with Claude")
    parser.add_argument("--dry-run", action="store_true", help="Preview first batch only")
    parser.add_argument("--reset", action="store_true", help="Clear progress and start over")
    args = parser.parse_args()

    run(dry_run=args.dry_run, reset=args.reset)


if __name__ == "__main__":
    main()
