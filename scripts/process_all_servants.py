"""
Process all servant data files and create structured JSON for MongoDB upload.

This script processes all servant JSON files in example_servant_data and creates
structured versions in the servants directory, ready for MongoDB upload.
"""

import json
import os
from pathlib import Path
from scripts.parse_servant_ascensions_corrected import create_structured_servant_data

def process_all_servants():
    """Process all servant JSON files and create structured data."""
    input_dir = Path('example_servant_data')
    output_dir = Path('servants')
    output_dir.mkdir(exist_ok=True)
    
    processed_count = 0
    skipped_count = 0
    errors = []
    
    for json_file in sorted(input_dir.glob('*.json')):
        # Skip variant files for now
        if 'with_variants' in json_file.name:
            continue
            
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                servant_data = json.load(f)
            
            structured_data = create_structured_servant_data(servant_data)
            
            if structured_data is None:
                print(f"Skipped {json_file.name} (collectionNo 1 or invalid)")
                skipped_count += 1
                continue
            
            # Save structured data
            collection_no = structured_data['collectionNo']
            output_file = output_dir / f"{collection_no}_structured.json"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(structured_data, f, ensure_ascii=False, indent=2)
            
            print(f"✓ {json_file.name} -> {output_file.name}")
            processed_count += 1
            
        except Exception as e:
            error_msg = f"✗ Error processing {json_file.name}: {e}"
            print(error_msg)
            errors.append(error_msg)
            skipped_count += 1
    
    # Summary
    print(f"\n{'='*50}")
    print(f"Processing Summary:")
    print(f"  Processed: {processed_count} servants")
    print(f"  Skipped: {skipped_count} servants")
    print(f"  Errors: {len(errors)}")
    
    if errors:
        print(f"\nErrors encountered:")
        for error in errors:
            print(f"  {error}")
    
    print(f"\nStructured data saved to: {output_dir.absolute()}")
    print(f"Ready for MongoDB upload!")

if __name__ == '__main__':
    process_all_servants()