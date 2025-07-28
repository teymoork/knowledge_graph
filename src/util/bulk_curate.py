import json
import os
import re

# --- Configuration ---
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SUGGESTED_MAP_PATH = os.path.join(PROJECT_ROOT, 'data', 'suggested_schema_map.json')
CURATED_MAP_PATH = os.path.join(PROJECT_ROOT, 'data', 'curated_schema_map.json')

def load_json(path, default_value):
    """Safely loads a JSON file."""
    if not os.path.exists(path):
        print(f"ERROR: File not found at {path}")
        return default_value
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"ERROR: Could not read or parse {path}: {e}")
        return default_value

def save_json(data, path):
    """Saves data to a JSON file."""
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_curated_term(farsi_term, original_english_term):
    """
    This function contains the consolidated expert rules to automatically curate a term.
    It returns a single, curated English string.
    """
    bad_categories = {"EVENT", "LEGAL", "SOCIAL", "LEADERSHIP", "FAMILY", "WORK", "POLITICAL", "JUDICIAL", "COMMUNICATION", "EDUCATION"}
    
    # --- Rule 1: Handle bad categories ---
    if original_english_term in bad_categories:
        # For these, we must flag for manual intervention.
        base_farsi = farsi_term.split('_')[0].split(' ')[0] # Get the first word
        return f"NEEDS_VERB_FOR_{base_farsi.upper()}"

    # --- Rule 2: Handle known special cases directly ---
    if farsi_term == 'آزاد_کرد':
        return 'RELEASED'
    if farsi_term == 'آمر':
        return 'ORDERED'
    if farsi_term == 'ابطال پروانه وکالت':
        return 'REVOKED_LICENSE_OF'
    if farsi_term == 'ابطال_کرد':
        return 'REVOKED'

    # --- Rule 3: General structural rules ---
    curated_term = original_english_term.upper().replace(" ", "_")

    # Passive voice check
    if farsi_term.endswith(("_شد", "_یافت", "_دیدند")) or "دید_از" in farsi_term:
        if not curated_term.startswith("WAS_"):
            curated_term = f"WAS_{curated_term}"
    
    # Active voice check for teaching
    if "آموزش_داد" in farsi_term:
        return "TAUGHT"

    # Remove prepositions from the Farsi term to see the core action
    farsi_core = re.sub(r'_(در|از|با|به|برای)$', '', farsi_term)
    
    # If the core action is different, it might indicate a need for review,
    # but for now, we trust the English term if it's not a bad category.

    # Final cleanup: remove any potential double "WAS_"
    if curated_term.startswith("WAS_WAS_"):
        curated_term = curated_term[4:]

    return curated_term

def bulk_curate_schema():
    """
    Main function to perform a full, automated curation pass on the schema map.
    """
    print("--- Starting Bulk Schema Curation ---")
    
    suggested_map = load_json(SUGGESTED_MAP_PATH, None)
    if suggested_map is None:
        return

    print(f"Loaded {len(suggested_map)} suggested mappings.")
    
    curated_map = {}
    placeholders_count = 0
    
    # Sort for consistent processing
    for farsi_term in sorted(suggested_map.keys()):
        original_english = suggested_map[farsi_term]
        curated_term = get_curated_term(farsi_term, original_english)
        curated_map[farsi_term] = curated_term
        
        if "NEEDS_VERB_FOR" in curated_term:
            placeholders_count += 1

    print("\nBulk curation pass complete.")
    print(f"Generated {len(curated_map)} curated mappings.")
    print(f"Flagged {placeholders_count} terms for manual review (containing 'NEEDS_VERB_FOR_...').")

    save_json(curated_map, CURATED_MAP_PATH)
    print(f"\nNew curated map saved to: {CURATED_MAP_PATH}")
    print("\nYour next step is to open this new file and manually edit the placeholder terms.")

if __name__ == "__main__":
    bulk_curate_schema()