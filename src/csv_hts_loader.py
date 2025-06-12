"""
CSV HTS Loader - Much more efficient than JSON approach

This loader works with the CSV file you have (3.7MB vs 30MB JSON).
Perfect for beginners - faster, smaller, and easier to understand.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Union
import os
from fuzzywuzzy import fuzz, process

class CSVHTSLoader:
    """
    Load and search HTS data from CSV file.
    
    This is much more efficient than the JSON approach:
    - Smaller file size (3.7MB vs 30MB)
    - Faster loading with pandas
    - Better search capabilities
    - Built-in data analysis tools
    """
    
    def __init__(self, csv_file_path: str = None):
        """
        Initialize the CSV loader.
        
        Args:
            csv_file_path: Path to your CSV file. If None, will look for uploaded file.
        """
        # Try to find the uploaded CSV file
        if csv_file_path is None:
            csv_file_path = self._find_uploaded_csv()
        
        self.csv_file_path = csv_file_path
        self.df = None  # Will store the pandas DataFrame
        self.search_index = None  # Will store search-optimized data
        
    def _find_uploaded_csv(self) -> str:
        """Try to find the uploaded CSV file."""
        possible_paths = [
            "hts_2025_revision_13.csv",  # Direct upload
            "data/hts_2025_revision_13.csv",  # In data folder
            "hts_data.csv",  # Generic name
            "data/hts_data.csv"  # Generic in data folder
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        # If not found, default to data folder
        return "data/hts_2025_revision_13_csv.csv"
    
    def load_data(self) -> bool:
        """
        Load HTS data from CSV file.
        
        Returns:
            bool: True if successful, False if error
        """
        try:
            print(f"📊 Loading HTS data from CSV: {self.csv_file_path}")
            
            # Load CSV with pandas - much faster than JSON!
            self.df = pd.read_csv(self.csv_file_path, dtype={
                'HTS Number': 'string',
                'Indent': 'int8',  # Small integer to save memory
                'Description': 'string',
                'Unit of Quantity': 'string', 
                'General Rate of Duty': 'string',
                'Special Rate of Duty': 'string',
                'Column 2 Rate of Duty': 'string',
                'Quota Quantity': 'string',
                'Additional Duties': 'string'
            })
            
            # Clean up the data
            self._clean_data()
            
            # Create search index
            self._build_search_index()
            
            print(f"✅ Successfully loaded {len(self.df):,} HTS records!")
            print(f"📏 File size: {os.path.getsize(self.csv_file_path) / (1024*1024):.1f} MB")
            print(f"💾 Memory usage: {self.df.memory_usage(deep=True).sum() / (1024*1024):.1f} MB")
            
            return True
            
        except FileNotFoundError:
            print(f"❌ Error: Could not find file {self.csv_file_path}")
            print("\n💡 Make sure your CSV file is in the right location:")
            print("   - Same folder as this script, OR")
            print("   - In a 'data' subfolder")
            return False
            
        except pd.errors.EmptyDataError:
            print("❌ Error: CSV file is empty")
            return False
            
        except Exception as e:
            print(f"❌ Unexpected error loading CSV: {e}")
            return False
    
    def _clean_data(self):
        """Clean and standardize the CSV data."""
        print("🧹 Cleaning data...")
        
        # Handle missing values
        self.df = self.df.fillna('')
        
        # Standardize HTS numbers (remove any spaces, make consistent)
        self.df['HTS Number'] = self.df['HTS Number'].str.strip()
        
        # Clean descriptions
        self.df['Description'] = self.df['Description'].str.strip()
        
        # Add convenience columns
        self.df['HTS_Clean'] = self.df['HTS Number'].str.replace('.', '').str.replace(' ', '')
        self.df['Description_Lower'] = self.df['Description'].str.lower()
        
        # Add chapter and section info
        self.df['Chapter'] = self.df['HTS Number'].str[:2]
        self.df['Heading'] = self.df['HTS Number'].str[:4].replace('', pd.NA)
        
        print(f"✅ Data cleaned: {len(self.df)} records ready")
    
    def _build_search_index(self):
        """Build search index for faster lookups."""
        print("🔍 Building search index...")
        
        # Create searchable text combining HTS number and description
        self.df['Search_Text'] = (
            self.df['HTS Number'].fillna('') + ' ' + 
            self.df['Description'].fillna('')
        ).str.lower()
        
        # Create index of unique descriptions for fuzzy matching
        unique_descriptions = self.df['Description'].dropna().unique()
        self.search_index = {desc.lower(): desc for desc in unique_descriptions}
        
        print("✅ Search index built")
    
    def explore_data_structure(self):
        """Explore the CSV data structure - much cleaner than JSON!"""
        if self.df is None:
            print("❌ No data loaded. Please run load_data() first.")
            return
        
        print("\n" + "="*60)
        print("📊 HTS CSV DATA EXPLORATION")
        print("="*60)
        
        # Basic info
        print(f"📈 Total records: {len(self.df):,}")
        print(f"📋 Columns: {len(self.df.columns)}")
        print(f"💾 Memory usage: {self.df.memory_usage(deep=True).sum() / (1024*1024):.1f} MB")
        
        # Show columns
        print(f"\n📝 Available Columns:")
        for col in self.df.columns:
            non_null = self.df[col].count()
            print(f"  • {col}: {non_null:,} non-null values")
        
        # Hierarchy breakdown
        print(f"\n🏗️ Hierarchy Structure:")
        indent_counts = self.df['Indent'].value_counts().sort_index()
        level_names = {0: "Chapter", 1: "Section", 2: "Subheading", 3: "Statistical"}
        
        for indent, count in indent_counts.items():
            level_name = level_names.get(indent, f"Level {indent}")
            print(f"  Indent {indent} ({level_name}): {count:,} records")
        
        # Chapter overview
        print(f"\n📚 Chapter Summary:")
        chapters = self.df[self.df['Indent'] == 0]['Chapter'].value_counts().head(10)
        for chapter, count in chapters.items():
            chapter_desc = self.df[
                (self.df['Chapter'] == chapter) & (self.df['Indent'] == 0)
            ]['Description'].iloc[0] if len(self.df[(self.df['Chapter'] == chapter) & (self.df['Indent'] == 0)]) > 0 else "Unknown"
            print(f"  Ch {chapter}: {chapter_desc[:50]}... ({count} items)")
    
    def search_simple(self, search_term: str, max_results: int = 10) -> pd.DataFrame:
        """
        Simple text search in descriptions - very fast with pandas!
        
        Args:
            search_term: What to search for
            max_results: Maximum results to return
            
        Returns:
            DataFrame with matching records
        """
        if self.df is None:
            print("❌ No data loaded. Please run load_data() first.")
            return pd.DataFrame()
        
        search_lower = search_term.lower()
        
        # Use pandas vectorized string operations - much faster than loops!
        matches = self.df[
            self.df['Description_Lower'].str.contains(search_lower, na=False, regex=False)
        ].head(max_results)
        
        print(f"🔍 Found {len(matches)} matches for '{search_term}'")
        return matches
    
    def search_fuzzy(self, search_term: str, max_results: int = 5, min_score: int = 70) -> pd.DataFrame:
        """
        Fuzzy search using fuzzywuzzy - finds similar matches even with typos.
        
        Args:
            search_term: What to search for
            max_results: Maximum results to return  
            min_score: Minimum similarity score (0-100)
            
        Returns:
            DataFrame with matching records and similarity scores
        """
        if self.df is None:
            print("❌ No data loaded. Please run load_data() first.")
            return pd.DataFrame()
        
        print(f"🧠 Fuzzy searching for '{search_term}'...")
        
        # Get all descriptions for fuzzy matching
        descriptions = self.df['Description'].dropna().tolist()
        
        # Find best matches
        matches = process.extract(search_term, descriptions, limit=max_results, scorer=fuzz.partial_ratio)
        
        # Filter by minimum score
        good_matches = [(desc, score) for desc, score in matches if score >= min_score]
        
        if not good_matches:
            print(f"❌ No fuzzy matches found above {min_score}% similarity")
            return pd.DataFrame()
        
        # Get the actual records
        result_rows = []
        for desc, score in good_matches:
            matching_rows = self.df[self.df['Description'] == desc]
            for _, row in matching_rows.iterrows():
                row_dict = row.to_dict()
                row_dict['Similarity_Score'] = score
                result_rows.append(row_dict)
        
        result_df = pd.DataFrame(result_rows)
        print(f"✅ Found {len(result_df)} fuzzy matches")
        return result_df
    
    def get_by_hts_code(self, hts_code: str) -> pd.DataFrame:
        """
        Look up specific HTS code.
        
        Args:
            hts_code: Exact HTS code to find
            
        Returns:
            DataFrame with matching record(s)
        """
        if self.df is None:
            print("❌ No data loaded. Please run load_data() first.")
            return pd.DataFrame()
        
        # Try exact match first
        exact_match = self.df[self.df['HTS Number'] == hts_code]
        
        if not exact_match.empty:
            return exact_match
        
        # Try partial match (in case of formatting differences)
        clean_code = hts_code.replace('.', '').replace(' ', '')
        partial_match = self.df[self.df['HTS_Clean'] == clean_code]
        
        return partial_match
    
    def get_chapter(self, chapter_num: str) -> pd.DataFrame:
        """Get all items in a specific chapter."""
        if self.df is None:
            print("❌ No data loaded. Please run load_data() first.")
            return pd.DataFrame()
        
        chapter_data = self.df[self.df['Chapter'] == chapter_num.zfill(2)]
        print(f"📖 Chapter {chapter_num}: {len(chapter_data)} items")
        return chapter_data
    
    def get_effective_duty_rate(self, hts_code: str) -> Dict[str, str]:
        """
        Get the effective duty rate for an HTS code, including inherited rates and cross-references.
        
        This handles multiple scenarios:
        1. Direct stored rates
        2. Inherited rates from parent codes
        3. Cross-references to other HTS codes (like parts/accessories)
        
        Args:
            hts_code: HTS code to look up
            
        Returns:
            Dict with effective rate information
        """
        if self.df is None:
            return {"error": "No data loaded"}
        
        # Find the specific record
        record = self.df[self.df['HTS Number'] == hts_code]
        
        if record.empty:
            return {"error": f"HTS code {hts_code} not found"}
        
        record = record.iloc[0]
        stored_rate = record['General Rate of Duty']
        
        # If the record has its own rate, use it
        if pd.notna(stored_rate) and stored_rate != '':
            # Check if it's a cross-reference (contains "applicable to")
            if "applicable to" in str(stored_rate).lower():
                return self._handle_cross_reference(hts_code, record, stored_rate)
            else:
                return {
                    "hts_code": hts_code,
                    "effective_rate": str(stored_rate),
                    "source": "stored",
                    "source_code": hts_code,
                    "description": record['Description']
                }
        
        # Walk up the hierarchy to find parent rate
        parent_rate_info = self._find_parent_with_rate(hts_code)
        
        if parent_rate_info:
            # Check if parent rate is a cross-reference
            if "applicable to" in str(parent_rate_info['rate']).lower():
                parent_record = self.df[self.df['HTS Number'] == parent_rate_info['source_code']].iloc[0]
                return self._handle_cross_reference(hts_code, parent_record, parent_rate_info['rate'])
            else:
                return {
                    "hts_code": hts_code,
                    "effective_rate": parent_rate_info['rate'],
                    "source": "inherited",
                    "source_code": parent_rate_info['source_code'],
                    "description": record['Description']
                }
        
        return {
            "hts_code": hts_code,
            "effective_rate": "Unknown",
            "source": "not_found",
            "source_code": None,
            "description": record['Description']
        }
    
    def _handle_cross_reference(self, original_hts: str, record: pd.Series, rate_text: str) -> Dict[str, str]:
        """
        Handle cross-references like "The rate applicable to the article of which it is a part or accessory"
        
        For parts/accessories (like 9017.90.01), we need to determine which main article
        this part belongs to, then use that article's rate.
        """
        description = record['Description']
        
        # For parts and accessories, try to find related main articles
        if "parts and accessories" in description.lower():
            # Extract potential reference codes from the rate description
            reference_codes = self._extract_reference_codes(rate_text, description)
            
            if reference_codes:
                # For demonstration, let's use the first reference or provide options
                return {
                    "hts_code": original_hts,
                    "effective_rate": "Depends on main article",
                    "source": "cross_reference",
                    "source_code": original_hts,
                    "description": description,
                    "reference_codes": reference_codes,
                    "explanation": f"Rate depends on which main article this is a part/accessory of: {', '.join(reference_codes)}"
                }
        
        return {
            "hts_code": original_hts,
            "effective_rate": "Cross-reference (manual lookup required)",
            "source": "cross_reference",
            "source_code": original_hts,
            "description": description,
            "explanation": rate_text
        }
    
    def _extract_reference_codes(self, rate_text: str, description: str) -> List[str]:
        """
        Extract HTS codes that this cross-reference might apply to.
        
        For 9017.90.01 parts, we can infer it applies to main 9017 articles.
        """
        reference_codes = []
        
        # For 9017.90.01 (parts and accessories), find main 9017 articles
        if "9017.90" in description or "parts and accessories" in description.lower():
            # Look for main 9017 codes (not parts codes)
            main_9017_codes = self.df[
                (self.df['HTS Number'].str.startswith('9017.', na=False)) &
                (~self.df['HTS Number'].str.startswith('9017.90', na=False)) &
                (self.df['Indent'] <= 2)  # Main articles, not statistical suffixes
            ]['HTS Number'].tolist()
            
            reference_codes.extend(main_9017_codes[:10])  # Limit to first 10
        
        return reference_codes
    
    def get_cross_reference_rates(self, parts_hts_code: str, main_article_hts: str) -> Dict[str, str]:
        """
        Get the effective rate for a parts/accessories code based on a specific main article.
        
        Example: get_cross_reference_rates("9017.90.01.36", "9017.20.80")
        This tells you the duty rate for parts of 9017.20.80 articles.
        
        Args:
            parts_hts_code: The parts/accessories HTS code
            main_article_hts: The main article this part belongs to
            
        Returns:
            Dict with the effective rate for this specific combination
        """
        if self.df is None:
            return {"error": "No data loaded"}
        
        # Get the main article's rate
        main_article_rate = self.get_effective_duty_rate(main_article_hts)
        
        if "error" in main_article_rate:
            return {"error": f"Main article {main_article_hts} not found"}
        
        # Get the parts record for description
        parts_record = self.df[self.df['HTS Number'] == parts_hts_code]
        if parts_record.empty:
            return {"error": f"Parts code {parts_hts_code} not found"}
        
        parts_record = parts_record.iloc[0]
        
        return {
            "parts_hts_code": parts_hts_code,
            "parts_description": parts_record['Description'],
            "main_article_hts": main_article_hts,
            "main_article_description": main_article_rate['description'],
            "effective_rate": main_article_rate['effective_rate'],
            "source": "cross_reference_resolved",
            "explanation": f"Parts of {main_article_hts} use the same rate as the main article"
        }
    
    def _find_parent_with_rate(self, hts_code: str) -> Optional[Dict]:
        """
        Walk up the HTS hierarchy to find a parent with a duty rate.
        
        This implements the inheritance logic:
        9017.20.80.40 → 9017.20.80 → 9017.20 → 9017 → 90
        """
        # Remove dots and work with clean numbers
        clean_code = hts_code.replace('.', '')
        
        # Try progressively shorter codes (walking up the hierarchy)
        for length in range(len(clean_code) - 1, 1, -1):
            parent_code = clean_code[:length]
            
            # Add dots back in the right places for lookup
            formatted_parent = self._format_hts_code(parent_code)
            
            # Look for this parent in the data
            parent_record = self.df[self.df['HTS Number'] == formatted_parent]
            
            if not parent_record.empty:
                parent = parent_record.iloc[0]
                rate = parent['General Rate of Duty']
                
                if pd.notna(rate) and rate != '':
                    return {
                        'rate': str(rate),
                        'source_code': formatted_parent
                    }
        
        return None
    
    def _format_hts_code(self, clean_code: str) -> str:
        """
        Format a clean HTS code back to the dotted format used in the data.
        
        Examples:
        901720 → 9017.20
        90172080 → 9017.20.80
        9017208040 → 9017.20.80.40
        """
        if len(clean_code) <= 4:
            return clean_code
        elif len(clean_code) <= 6:
            return f"{clean_code[:4]}.{clean_code[4:]}"
        elif len(clean_code) <= 8:
            return f"{clean_code[:4]}.{clean_code[4:6]}.{clean_code[6:]}"
        else:
            return f"{clean_code[:4]}.{clean_code[4:6]}.{clean_code[6:8]}.{clean_code[8:]}"
    
    def show_examples(self, search_term: str, max_examples: int = 5):
        """Show search examples in a nice format with effective duty rates."""
        matches = self.search_simple(search_term, max_examples)
        
        if matches.empty:
            print(f"❌ No examples found for '{search_term}'")
            return
        
        print(f"\n📋 Examples for '{search_term}':")
        print("-" * 80)
        
        for i, (_, row) in enumerate(matches.iterrows(), 1):
            hts_code = row['HTS Number']
            
            # Get effective duty rate
            duty_info = self.get_effective_duty_rate(hts_code)
            
            print(f"{i}. HTS: {hts_code}")
            print(f"   Description: {row['Description']}")
            print(f"   Indent: {row['Indent']}")
            
            # Show both stored and effective rates
            stored_rate = row['General Rate of Duty']
            if pd.isna(stored_rate) or stored_rate == '':
                print(f"   Stored Duty: null")
            else:
                print(f"   Stored Duty: {stored_rate}")
            
            if duty_info.get('source') == 'inherited':
                print(f"   💰 Effective Duty: {duty_info['effective_rate']} (inherited from {duty_info['source_code']})")
            elif duty_info.get('source') == 'stored':
                print(f"   💰 Effective Duty: {duty_info['effective_rate']} (direct)")
            else:
                print(f"   💰 Effective Duty: {duty_info['effective_rate']}")
            
            if row['Unit of Quantity']:
                print(f"   Unit: {row['Unit of Quantity']}")
            print()
    
    def lookup_with_effective_rate(self, hts_code: str) -> Dict:
        """
        Complete lookup with effective duty rate - perfect for your AI agent!
        
        Args:
            hts_code: HTS code to look up
            
        Returns:
            Complete information including effective duty
        """
        # Get basic record info
        record = self.get_by_hts_code(hts_code)
        
        if record.empty:
            return {"error": f"HTS code {hts_code} not found"}
        
        record = record.iloc[0]
        
        # Get effective duty rate
        duty_info = self.get_effective_duty_rate(hts_code)
        
        # Combine all information
        result = {
            "hts_code": hts_code,
            "description": record['Description'],
            "indent": record['Indent'],
            "unit": record['Unit of Quantity'],
            "stored_general_duty": record['General Rate of Duty'],
            "stored_special_duty": record['Special Rate of Duty'],
            "effective_general_duty": duty_info['effective_rate'],
            "duty_source": duty_info['source'],
            "duty_source_code": duty_info.get('source_code'),
            "chapter": record.get('Chapter', ''),
            "heading": record.get('Heading', '')
        }
        
        return result

# Example usage
def main():
    """Example of using the CSV HTS Loader."""
    print("🚀 CSV HTS Loader - Much Better Than JSON!")
    print("=" * 50)
    
    # Initialize and load
    loader = CSVHTSLoader()
    
    if loader.load_data():
        # Explore structure
        loader.explore_data_structure()
        
        # Try some searches
        print("\n" + "="*50)
        print("🔍 SEARCH EXAMPLES")
        print("="*50)
        
        # Simple search
        loader.show_examples("computer", 3)
        
        # Fuzzy search
        print("\n🧠 Fuzzy Search Example:")
        fuzzy_results = loader.search_fuzzy("computr", max_results=3)  # Typo on purpose
        if not fuzzy_results.empty:
            for _, row in fuzzy_results.iterrows():
                print(f"  {row['Similarity_Score']}% - {row['HTS Number']}: {row['Description'][:60]}...")
        
        # HTS lookup
        print("\n🎯 Specific HTS Lookup:")
        specific = loader.get_by_hts_code("8471.30.01")
        if not specific.empty:
            row = specific.iloc[0]
            print(f"  Found: {row['Description']}")
            print(f"  Duty: {row['General Rate of Duty']}")
        
        print("\n✅ CSV loader demo complete!")
        print("This is MUCH faster and more efficient than JSON!")
        
    else:
        print("❌ Could not load CSV data")

if __name__ == "__main__":
    main()