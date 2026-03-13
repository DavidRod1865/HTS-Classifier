"""
Batch-enrich HTS descriptions with commercial product language using OpenAI.

Reads the source CSV, groups entries by chapter, sends batches to OpenAI for
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
import threading
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger(__name__)

ENRICHMENT_MODEL = os.getenv("ENRICHMENT_MODEL", "gpt-4o-mini")
BATCH_SIZE = 50  # entries per API call
MAX_RETRIES = 3
MAX_WORKERS = 5  # concurrent API calls

CSV_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "hts_2026_revision_4.csv"
)
OUTPUT_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "hts_2026_revision_4_enriched.csv"
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
        'Respond with a JSON object containing a "results" array, one object per entry, in order:\n'
        '{"results": [{"hts_code": "...", "enriched_text": "..."}, ...]}'
    )


def parse_response(text, entries):
    """Parse JSON response, with fallbacks for each entry."""
    import re
    results = {}

    try:
        data = json.loads(text)
        # Support both {"results": [...]} and bare [...]
        if isinstance(data, dict) and "results" in data:
            parsed = data["results"]
        elif isinstance(data, list):
            parsed = data
        else:
            parsed = []
    except json.JSONDecodeError:
        # Fallback: try to extract array from text
        try:
            match = re.search(r"\[.*\]", text, re.DOTALL)
            parsed = json.loads(match.group()) if match else []
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
    """Send one batch to OpenAI and return enriched texts."""
    prompt = build_prompt(entries, chapter_context)

    if dry_run:
        logger.info(f"[DRY RUN] Would send {len(entries)} entries to {ENRICHMENT_MODEL}")
        logger.info(f"Prompt preview:\n{prompt[:500]}...")
        return {e["HTS Number"].strip(): "[dry run placeholder]" for e in entries}

    for attempt in range(MAX_RETRIES):
        try:
            response = client.chat.completions.create(
                model=ENRICHMENT_MODEL,
                max_completion_tokens=200 * len(entries),
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )
            return parse_response(response.choices[0].message.content, entries)
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
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: Set OPENAI_API_KEY in your environment.", file=sys.stderr)
        sys.exit(1)

    client = OpenAI(api_key=api_key)

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

    # Build list of all batches to process
    all_batches = []
    for chapter in sorted(chapters.keys()):
        entries = chapters[chapter]
        first_path = (entries[0].get("Context Path") or "").strip()
        chapter_context = first_path.split(" > ")[0] if first_path else f"Chapter {chapter}"

        for i in range(0, len(entries), BATCH_SIZE):
            batch = entries[i:i + BATCH_SIZE]
            unenriched = [e for e in batch if e["HTS Number"].strip() not in enriched]
            if unenriched:
                all_batches.append((chapter, i // BATCH_SIZE + 1, unenriched, chapter_context))

    total_to_do = len(leaf_nodes)
    total_processed = len(enriched)
    logger.info(f"  {len(all_batches)} batches to process with {MAX_WORKERS} workers")

    if dry_run and all_batches:
        ch, bn, entries, ctx = all_batches[0]
        enrich_batch(client, entries, ctx, dry_run=True)
        logger.info("Dry run — stopping after first batch.")
        return

    # Process batches concurrently
    lock = threading.Lock()

    def process_batch(batch_info):
        ch, bn, entries, ctx = batch_info
        results = enrich_batch(client, entries, ctx)
        return (ch, bn, results)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(process_batch, b): b for b in all_batches}
        batch_count = 0

        for future in as_completed(futures):
            ch, bn, results = future.result()
            batch_count += 1

            with lock:
                enriched.update(results)
                total_processed += len(results)
                progress["enriched"] = enriched

                # Save progress every 5 batches to reduce I/O
                if batch_count % 5 == 0 or batch_count == len(all_batches):
                    save_progress(progress)

            logger.info(
                f"[{batch_count}/{len(all_batches)}] Ch {ch} batch {bn} — "
                f"{len(results)} entries ({total_processed}/{total_to_do} total)"
            )

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
    parser = argparse.ArgumentParser(description="Enrich HTS descriptions with OpenAI")
    parser.add_argument("--dry-run", action="store_true", help="Preview first batch only")
    parser.add_argument("--reset", action="store_true", help="Clear progress and start over")
    args = parser.parse_args()

    run(dry_run=args.dry_run, reset=args.reset)


if __name__ == "__main__":
    main()
