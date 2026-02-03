#!/usr/bin/env python3
"""
One-time script: embed HTS leaf nodes and upload to Pinecone.

Run locally whenever the CSV changes:
    cd backend
    OPENAI_API_KEY=sk-... PINECONE_API_KEY=pc-... python src/embed_and_upload.py

Creates (or reuses) a Pinecone index named "hts-codes" with 1536-dim vectors
(OpenAI text-embedding-3-small). Upserts are idempotent by ID, so re-running
is safe and only overwrites changed records.
"""

import os
import sys
import csv
import time
from dotenv import load_dotenv
from openai import OpenAI
from pinecone import Pinecone, ServerlessSpec

load_dotenv()

INDEX_NAME = "hts-codes"
EMBEDDING_MODEL = "text-embedding-3-small"
BATCH_SIZE = 100
CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "hts_2025_revision_13.csv")


def build_text(row):
    """Text that gets embedded — the only thing that affects search quality."""
    parts = []
    for field in ("Enhanced Description", "Search Keywords", "Context Path"):
        val = (row.get(field) or "").strip()
        if val:
            parts.append(val)
    return " ".join(parts)


def build_metadata(row):
    """Stored alongside the vector; returned on query. Duty rates live here."""
    code = (row.get("HTS Number") or "").strip()
    return {
        "hts_code": code,
        "description": (row.get("Enhanced Description") or "").strip(),
        "general_rate": (row.get("General Rate of Duty") or "").strip(),
        "special_rate": (row.get("Special Rate of Duty") or "").strip(),
        "unit": (row.get("Unit of Quantity") or "").strip(),
        "chapter": code[:2] if len(code) >= 2 else "",
        "context_path": (row.get("Context Path") or "").strip(),
    }


def main():
    openai_key = os.getenv("OPENAI_API_KEY")
    pinecone_key = os.getenv("PINECONE_API_KEY")
    if not openai_key or not pinecone_key:
        print("ERROR: Set OPENAI_API_KEY and PINECONE_API_KEY in your environment.")
        sys.exit(1)

    client = OpenAI(api_key=openai_key, max_retries=10)
    pc = Pinecone(api_key=pinecone_key)

    # Ensure index exists with correct dimensions
    existing = [idx.name for idx in pc.list_indexes()]
    if INDEX_NAME not in existing:
        print(f"Creating Pinecone index '{INDEX_NAME}' (1536 dims, cosine)...")
        pc.create_index(
            name=INDEX_NAME,
            dimension=1536,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
        print("Waiting for index to initialize...")
        time.sleep(10)
    else:
        print(f"Index '{INDEX_NAME}' already exists. Will upsert into it.")

    index = pc.Index(INDEX_NAME)

    # Load CSV, keep only leaf nodes with an HTS number
    print(f"\nLoading {CSV_PATH}...")
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        rows = [
            r for r in csv.DictReader(f)
            if (r.get("Is Leaf Node") or "").strip() == "Yes"
            and (r.get("HTS Number") or "").strip()
        ]
    print(f"  {len(rows)} leaf nodes to embed")

    # Embed and upload in batches
    uploaded = 0
    for i in range(0, len(rows), BATCH_SIZE):
        batch = rows[i : i + BATCH_SIZE]

        # Build (row, text) pairs, skipping anything with empty text
        valid = [(r, build_text(r)) for r in batch]
        valid = [(r, t) for r, t in valid if t.strip()]
        if not valid:
            continue

        # Embed via OpenAI
        resp = client.embeddings.create(
            input=[t for _, t in valid],
            model=EMBEDDING_MODEL,
        )

        # Assemble vectors for upsert
        vectors = [
            {
                "id": f"hts_{row['HTS Number'].strip()}",
                "values": resp.data[j].embedding,
                "metadata": build_metadata(row),
            }
            for j, (row, _) in enumerate(valid)
        ]

        index.upsert(vectors=vectors)
        uploaded += len(vectors)
        print(f"  {uploaded}/{len(rows)} uploaded")

    print(f"\nDone. {uploaded} vectors in '{INDEX_NAME}'.")


if __name__ == "__main__":
    main()
