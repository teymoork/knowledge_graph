import json
import os
import ijson
from tqdm import tqdm

# --- Configuration ---
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
# --- MODIFIED: Point to the final curated map ---
SCHEMA_MAP_PATH = os.path.join(PROJECT_ROOT, 'data', 'curated_schema_map.json')
OLD_GRAPH_PATH = os.path.join(PROJECT_ROOT, 'data', 'extracted_graph.json.250728.full')
NEW_GRAPH_PATH = os.path.join(PROJECT_ROOT, 'data', 'extracted_graph_english_schema.json')

def translate_graph_data():
    """
    Reads the old graph data, translates relationship types using the FINAL CURATED schema map,
    and writes the result to a new file.
    """
    print("Starting translation of existing graph data using FINAL curated map...")

    # 1. Load the Farsi-to-English schema map
    try:
        with open(SCHEMA_MAP_PATH, 'r', encoding='utf-8') as f:
            schema_map = json.load(f)
        print(f"Successfully loaded curated schema map with {len(schema_map)} entries.")
    except FileNotFoundError:
        print(f"ERROR: Curated schema map file not found at {SCHEMA_MAP_PATH}")
        return
    except json.JSONDecodeError:
        print(f"ERROR: Could not decode JSON from {SCHEMA_MAP_PATH}")
        return

    # 2. Stream the old graph file and translate each relationship
    translated_relationships = []
    unmapped_relations = set()
    processed_count = 0

    print(f"Reading old graph data from: {OLD_GRAPH_PATH}")
    try:
        with open(OLD_GRAPH_PATH, 'r', encoding='utf-8') as f:
            relationships = ijson.items(f, 'graph.item')
            
            print("Processing relationships... (This may take a while for large files)")
            for rel in tqdm(relationships, desc="Translating relationships"):
                processed_count += 1
                farsi_relation = rel.get('relation')

                if farsi_relation in schema_map:
                    rel['relation'] = schema_map[farsi_relation]
                    translated_relationships.append(rel)
                elif farsi_relation:
                    unmapped_relations.add(farsi_relation)
    
    except FileNotFoundError:
        print(f"ERROR: Old graph file not found at {OLD_GRAPH_PATH}")
        return
    except Exception as e:
        print(f"An error occurred while reading the old graph file: {e}")
        return

    print(f"\nProcessed {processed_count} total relationships from the source file.")
    print(f"Successfully translated {len(translated_relationships)} relationships.")
    
    if unmapped_relations:
        print(f"\nWARNING: Found {len(unmapped_relations)} relationship types in the data that were not in the schema map.")
        print("These relationships were SKIPPED. First 5 examples:")
        for i, rel_type in enumerate(list(unmapped_relations)):
            if i >= 5: break
            print(f"- {rel_type}")

    # 3. Write the translated data to the new file
    print(f"\nWriting translated graph to new file: {NEW_GRAPH_PATH}")
    try:
        with open(NEW_GRAPH_PATH, 'w', encoding='utf-8') as f:
            json.dump({"graph": translated_relationships}, f, ensure_ascii=False, indent=2)
        print("Translation complete. New file saved successfully.")
    except Exception as e:
        print(f"ERROR: Could not write to the new graph file. {e}")


if __name__ == "__main__":
    translate_graph_data()
