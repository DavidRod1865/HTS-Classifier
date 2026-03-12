"""
CSV update flow — validate, replace CSV on disk, re-populate Pinecone, reload in-memory lookup.

Called by the /api/update-csv endpoint when an admin uploads a new HTS CSV.
"""

import os
import csv
import io
import logging

logger = logging.getLogger(__name__)

CSV_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "hts_2025_revision_13.csv"
)

REQUIRED_COLUMNS = {
    "HTS Number",
    "Is Leaf Node",
    "Enhanced Description",
    "General Rate of Duty",
    "Special Rate of Duty",
    "Unit of Quantity",
    "Context Path",
    "Search Keywords",
}


def validate_csv(csv_bytes):
    """Check that the uploaded CSV has the required columns. Returns (ok, error_msg)."""
    try:
        text = csv_bytes.decode("utf-8")
        reader = csv.DictReader(io.StringIO(text))
        headers = set(reader.fieldnames or [])
        missing = REQUIRED_COLUMNS - headers
        if missing:
            return False, f"Missing required columns: {', '.join(sorted(missing))}"
        return True, None
    except Exception as e:
        return False, f"Failed to parse CSV: {e}"


def update_csv_and_index(csv_bytes, search_instance):
    """
    Full update flow:
        1. Validate CSV structure
        2. Overwrite the CSV file on disk
        3. Re-populate the Pinecone index
        4. Reload the in-memory HTS lookup

    Args:
        csv_bytes: raw bytes of the uploaded CSV
        search_instance: HTSSearch instance (for reload_csv())

    Returns:
        { status, records_processed } or raises ValueError on validation failure
    """
    # 1. Validate
    ok, error = validate_csv(csv_bytes)
    if not ok:
        raise ValueError(error)

    # 2. Write to disk
    logger.info(f"Writing new CSV to {CSV_PATH}")
    with open(CSV_PATH, "wb") as f:
        f.write(csv_bytes)

    # 3. Re-populate Pinecone index
    from embed_and_upload import populate_index
    records = populate_index(CSV_PATH)

    # 4. Reload in-memory lookup
    search_instance.reload_csv()

    return {"status": "complete", "records_processed": records}
