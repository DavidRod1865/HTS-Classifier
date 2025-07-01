import pandas as pd
import json
import time
from typing import List, Dict, Any
import hashlib

def load_and_prepare_hts_data(csv_path: str) -> pd.DataFrame:
    """Load and clean the HTS CSV data"""
    df = pd.read_csv(csv_path)
    
    # Fill NaN values with empty strings for text fields
    text_columns = ['Original Description', 'Enhanced Description', 'Context Path', 
                   'Search Keywords', 'Category', 'Unit of Quantity', 
                   'General Rate of Duty', 'Special Rate of Duty', 'Column 2 Rate of Duty',
                   'Quota Quantity', 'Additional Duties']
    
    for col in text_columns:
        df[col] = df[col].fillna('')
    
    # Fill NaN values with 0 for numeric fields
    df['Word Count'] = df['Word Count'].fillna(0)
    df['Indent'] = df['Indent'].fillna(0)
    df['Level'] = df['Level'].fillna(0)
    
    # Convert boolean-like fields
    df['Has Duty Info'] = df['Has Duty Info'].fillna('False')
    df['Is Leaf Node'] = df['Is Leaf Node'].fillna('False')
    
    return df

def create_searchable_text(row) -> str:
    """Combine relevant fields into searchable text for embedding"""
    text_parts = []
    
    # Primary description fields
    if row['Original Description']:
        text_parts.append(f"Description: {row['Original Description']}")
    
    if row['Enhanced Description'] and row['Enhanced Description'] != row['Original Description']:
        text_parts.append(f"Enhanced: {row['Enhanced Description']}")
    
    # Context and keywords
    if row['Context Path']:
        text_parts.append(f"Context: {row['Context Path']}")
    
    if row['Search Keywords']:
        text_parts.append(f"Keywords: {row['Search Keywords']}")
    
    # Category information
    if row['Category']:
        text_parts.append(f"Category: {row['Category']}")
    
    # HTS Number for exact matching
    text_parts.append(f"HTS: {row['HTS Number']}")
    
    return " | ".join(text_parts)

def create_metadata(row) -> Dict[str, Any]:
    """Create metadata for Pinecone storage"""
    import pandas as pd
    # Use field names that match commodity_rag_search.py expectations
    metadata = {
        'hts_code': str(row['HTS Number']),
        'description': str(row['Enhanced Description'])[:1000],  # Main description field
        'original_description': str(row['Original Description'])[:1000],
        'category': str(row['Category']),
        'level': int(row['Level']),
        'indent': int(row['Indent']),
        'is_leaf_node': str(row['Is Leaf Node']).lower() == 'true',
        'has_duty_info': str(row['Has Duty Info']).lower() == 'true',
        'word_count': int(row['Word Count'])
    }
    
    # Add duty information with correct field names (handle NaN/null values)
    if pd.notna(row['General Rate of Duty']) and str(row['General Rate of Duty']).strip():
        metadata['general_rate'] = str(row['General Rate of Duty'])[:200]
    
    if pd.notna(row['Special Rate of Duty']) and str(row['Special Rate of Duty']).strip():
        metadata['special_rate'] = str(row['Special Rate of Duty'])[:200]
    
    if pd.notna(row['Unit of Quantity']) and str(row['Unit of Quantity']).strip():
        metadata['unit'] = str(row['Unit of Quantity'])[:100]
    
    # Add context path for hierarchical searches
    if pd.notna(row['Context Path']) and str(row['Context Path']).strip():
        metadata['context_path'] = str(row['Context Path'])[:500]
    
    # Add search keywords
    if pd.notna(row['Search Keywords']) and str(row['Search Keywords']).strip():
        metadata['search_keywords'] = str(row['Search Keywords'])[:500]
    
    # Extract chapter and heading from HTS Number
    hts_number = str(row['HTS Number'])
    if hts_number and len(hts_number) >= 2:
        metadata['chapter'] = hts_number[:2]
    if hts_number and len(hts_number) >= 4:
        metadata['heading'] = hts_number[:4]
    
    return metadata

def generate_vector_id(row) -> str:
    """Generate a unique, deterministic ID for each vector"""
    # Use HTS Number as primary identifier, with row index as backup
    base_id = f"hts_{row['HTS Number']}"
    # Create hash to ensure uniqueness and handle special characters
    return hashlib.md5(base_id.encode()).hexdigest()[:16]

def prepare_pinecone_data(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Transform DataFrame into Pinecone-ready format"""
    pinecone_data = []
    
    for idx, row in df.iterrows():
        # Create the text that will be embedded
        searchable_text = create_searchable_text(row)
        
        # Skip empty records
        if not searchable_text.strip():
            continue
        
        # Create the record
        record = {
            'id': generate_vector_id(row),
            'text_to_embed': searchable_text,  # This will be embedded
            'metadata': create_metadata(row)
        }
        
        pinecone_data.append(record)
        
        # Progress indicator
        if (idx + 1) % 1000 == 0:
            print(f"Processed {idx + 1} records...")
    
    return pinecone_data

def create_batches(data: List[Dict], batch_size: int = 100) -> List[List[Dict]]:
    """Split data into batches for Pinecone upload"""
    batches = []
    for i in range(0, len(data), batch_size):
        batch = data[i:i + batch_size]
        batches.append(batch)
    return batches

def save_prepared_data(data: List[Dict], filename: str = 'hts_pinecone_ready.json'):
    """Save the prepared data to JSON for inspection/backup"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(data)} records to {filename}")

# Example usage and batch processing template
def process_hts_for_pinecone(csv_path: str, batch_size: int = 100):
    """Complete pipeline to process HTS data for Pinecone"""
    
    print("Loading HTS data...")
    df = load_and_prepare_hts_data(csv_path)
    print(f"Loaded {len(df)} records")
    
    print("Transforming data for Pinecone...")
    pinecone_data = prepare_pinecone_data(df)
    print(f"Prepared {len(pinecone_data)} records for Pinecone")
    
    print("Creating batches...")
    batches = create_batches(pinecone_data, batch_size)
    print(f"Created {len(batches)} batches of ~{batch_size} records each")
    
    # Save the prepared data
    save_prepared_data(pinecone_data)
    
    return batches, pinecone_data

# Sample function to show what the data looks like
def preview_transformed_data(csv_path: str, num_samples: int = 3):
    """Preview what the transformed data looks like"""
    df = load_and_prepare_hts_data(csv_path)
    sample_data = prepare_pinecone_data(df.head(num_samples))
    
    print("=== SAMPLE TRANSFORMED DATA ===")
    for i, record in enumerate(sample_data):
        print(f"\n--- Record {i+1} ---")
        print(f"ID: {record['id']}")
        print(f"Text to embed: {record['text_to_embed'][:200]}...")
        print(f"Metadata keys: {list(record['metadata'].keys())}")
        print(f"Sample metadata: {dict(list(record['metadata'].items())[:3])}")

if __name__ == "__main__":
    # Example usage
    csv_file = "hts_2025_revision_13.csv"
    
    # Preview the transformation
    print("Previewing transformation...")
    preview_transformed_data(csv_file)
    
    # Full processing
    print("\nProcessing full dataset...")
    batches, full_data = process_hts_for_pinecone(csv_file, batch_size=100)
    
    print(f"\nReady for Pinecone!")
    print(f"- {len(full_data)} total records")
    print(f"- {len(batches)} batches")
    print(f"- Data saved to 'hts_pinecone_ready.json'")
    print(f"- Each record has 'id', 'text_to_embed', and 'metadata' fields")
    print(f"- Ready for embedding generation and Pinecone upload")