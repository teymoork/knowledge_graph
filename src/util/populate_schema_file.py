import json
import os

# Define the paths
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
# --- MODIFIED: Point to the final curated map ---
SCHEMA_MAP_PATH = os.path.join(PROJECT_ROOT, 'data', 'curated_schema_map.json')
GRAPH_SCHEMA_PATH = os.path.join(PROJECT_ROOT, 'src', 'graph_schema.py')

def update_schema_file():
    """
    Reads the FINAL CURATED schema map and updates the RELATIONSHIP_TYPES
    list in the src/graph_schema.py file.
    """
    print("Starting schema file update process with FINAL curated map...")

    # 1. Read the schema map and get unique English relationship types
    try:
        with open(SCHEMA_MAP_PATH, 'r', encoding='utf-8') as f:
            schema_map = json.load(f)
        
        # Using a set to get unique values, then converting to a sorted list
        unique_english_types = sorted(list(set(schema_map.values())))
        print(f"Found {len(unique_english_types)} unique English relationship types in the curated map.")

    except FileNotFoundError:
        print(f"ERROR: Curated schema map file not found at {SCHEMA_MAP_PATH}")
        return
    except json.JSONDecodeError:
        print(f"ERROR: Could not decode JSON from {SCHEMA_MAP_PATH}")
        return

    # 2. Read the graph_schema.py file content
    try:
        with open(GRAPH_SCHEMA_PATH, 'r', encoding='utf-8') as f:
            schema_file_lines = f.readlines()
    except FileNotFoundError:
        print(f"ERROR: Graph schema file not found at {GRAPH_SCHEMA_PATH}")
        return

    # 3. Prepare the new content for the RELATIONSHIP_TYPES list
    new_list_content = "RELATIONSHIP_TYPES = [\n"
    for rel_type in unique_english_types:
        new_list_content += f'    "{rel_type}",\n'
    new_list_content += "]\n"

    # 4. Find and replace the old list in the file content
    output_lines = []
    in_list = False
    list_found = False
    for line in schema_file_lines:
        if line.strip().startswith("RELATIONSHIP_TYPES = ["):
            output_lines.append(new_list_content)
            in_list = True
            list_found = True
        elif in_list and line.strip() == "]":
            in_list = False
            continue
        elif not in_list:
            output_lines.append(line)

    if not list_found:
        print("ERROR: Could not find the 'RELATIONSHIP_TYPES = [' line in the schema file.")
        return

    # 5. Write the updated content back to the file
    try:
        with open(GRAPH_SCHEMA_PATH, 'w', encoding='utf-8') as f:
            f.writelines(output_lines)
        print(f"Successfully updated {GRAPH_SCHEMA_PATH} with the final curated relationship types.")
    except Exception as e:
        print(f"ERROR: Could not write to the schema file. {e}")


if __name__ == "__main__":
    update_schema_file()