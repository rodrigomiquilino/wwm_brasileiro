import csv
import sys
import os
from collections import defaultdict

def load_dictionary(filepath):
    # List of (term, translation) tuples to preserve duplicates if they exist with diff translations
    dictionary = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter='\t')
            header = next(reader, None) # Skip header
            for row in reader:
                if len(row) >= 2:
                    term = row[0].strip()
                    translation = row[1].strip()
                    if term: # Only add non-empty terms
                        dictionary.append((term, translation))
    except Exception as e:
        print(f"Error reading dictionary: {e}")
        sys.exit(1)
    return dictionary

def load_translations(filepath):
    text_to_ids = {}
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter='\t')
            header = next(reader, None) # Skip header
            for row in reader:
                if len(row) >= 2:
                    id_val = row[0].strip()
                    text = row[1].strip()
                    if text:
                        if text not in text_to_ids:
                            text_to_ids[text] = []
                        text_to_ids[text].append(id_val)
    except Exception as e:
        print(f"Error reading translations: {e}")
        sys.exit(1)
    return text_to_ids

def find_matches(dictionary, text_to_ids, output_file):
    print(f"Processing {len(text_to_ids)} unique texts against {len(dictionary)} dictionary terms...")
    
    # Map (term, translation) -> set of IDs
    # We group by both to handle cases where the same term might have multiple entries/translations
    match_map = defaultdict(set)
    
    match_count = 0
    
    # Optimization: Convert dictionary to a list for faster iteration if needed, 
    # but here we iterate it for every text.
    
    for text, ids in text_to_ids.items():
        # Check each dictionary term against the text
        for term, translation in dictionary:
            if term in text:
                match_map[(term, translation)].update(ids)
                match_count += 1
                    
    print(f"Done processing. Found matches for {len(match_map)} dictionary entries.")
    
    with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f, delimiter='\t')
        # Header: EN, RUS, ID
        writer.writerow(['EN', 'RUS', 'ID'])
        
        # Sort by term for consistent output
        sorted_keys = sorted(match_map.keys(), key=lambda x: x[0])
        
        for term, translation in sorted_keys:
            # Sort IDs for consistent output
            ids_list = sorted(list(match_map[(term, translation)]))
            ids_str = ';'.join(ids_list)
            
            writer.writerow([term, translation, ids_str])

    print(f"Saved to {output_file}")

def main():
    base_dir = os.getcwd()
    dict_path = os.path.join(base_dir, 'docs', 'dictionary.tsv')
    trans_path = os.path.join(base_dir, 'translation_en.tsv')
    output_path = os.path.join(base_dir, 'dictionary_matches.tsv')
    
    if not os.path.exists(dict_path):
        print(f"Dictionary not found at {dict_path}")
        return
    if not os.path.exists(trans_path):
        print(f"Translation file not found at {trans_path}")
        return
        
    dictionary = load_dictionary(dict_path)
    text_to_ids = load_translations(trans_path)
    
    find_matches(dictionary, text_to_ids, output_path)

if __name__ == "__main__":
    main()
