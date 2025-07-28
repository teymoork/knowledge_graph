import os
import ijson
import json
from dotenv import load_dotenv
import google.generativeai as genai
import time
from tqdm import tqdm

# --- Configuration ---
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

# --- Paths ---
SOURCE_JSON_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'extracted_graph.json.250728.full')
DRAFT_MAP_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'ai_draft_schema_map.json')
FINAL_MAP_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'suggested_schema_map.json')
BATCH_SIZE = 100

# --- Utility Functions ---
def get_unique_farsi_relations(file_path):
    """Scans the JSON file for unique, valid Farsi relationship strings."""
    print(f"Scanning {file_path} for unique relationship types...")
    unique_relations = set()
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            relationships = ijson.items(f, 'graph.item')
            for rel in relationships:
                relation_value = rel.get('relation')
                if isinstance(relation_value, str) and relation_value.strip():
                    unique_relations.add(relation_value)
        print(f"Found {len(unique_relations)} unique, valid relationship types.")
        return sorted(list(unique_relations))
    except Exception as e:
        print(f"Error reading source JSON: {e}")
        return None

def call_generative_model(prompt, model):
    """A robust function to call the generative model with self-correction."""
    max_retries = 3
    current_prompt = prompt
    for i in range(max_retries):
        try:
            response = model.generate_content(current_prompt)
            cleaned_response = response.text.strip().replace("```json", "").replace("```", "")
            return json.loads(cleaned_response)
        except json.JSONDecodeError as e:
            tqdm.write(f"  - JSON Decode Error: {e}. Retrying with self-correction...")
            current_prompt = f"Your previous response was not valid JSON. Please fix it. ERROR: {e}\n\nFAULTY TEXT:\n{response.text}"
            time.sleep(2)
        except Exception as e:
            tqdm.write(f"  - An unexpected API error occurred: {e}. Retrying...")
            time.sleep(2)
    tqdm.write("  - FAILED to get valid JSON after multiple retries.")
    return None

# --- Stage 1: Draft Mapping in Batches ---
def generate_draft_map(farsi_relations, model):
    """Generates a draft Farsi-to-English map in batches."""
    print("\n--- Stage 1: Generating Draft Farsi-to-English Map in Batches ---")
    draft_map = {}
    batches = [farsi_relations[i:i + BATCH_SIZE] for i in range(0, len(farsi_relations), BATCH_SIZE)]
    
    for batch in tqdm(batches, desc="Stage 1: Draft Mapping"):
        prompt = f"""
        You are a data architect. Your task is to translate a list of Farsi relationship types into English.
        RULES:
        1. Output MUST be a single, valid JSON object.
        2. Keys are the original Farsi types; values are the English translations in UPPER_SNAKE_CASE.
        3. Translate the conceptual meaning. Do not just transliterate.
        4. Produce ONLY the JSON object.
        Farsi Terms: {json.dumps(batch, ensure_ascii=False)}
        """
        batch_map = call_generative_model(prompt, model)
        if batch_map:
            draft_map.update(batch_map)
        time.sleep(1)
        
    print(f"Stage 1 Complete. Draft map contains {len(draft_map)} entries.")
    return draft_map

# --- Stage 2: Consolidate English Terms ---
def consolidate_english_terms(english_terms, model):
    """Groups similar English terms and assigns a canonical name for each group."""
    print("\n--- Stage 2: Consolidating English Terms for Standardization ---")
    prompt = f"""
    You are a data architect. Your task is to consolidate the following list of English relationship types.
    Group them by semantic meaning and provide a single canonical name for each group.
    RULES:
    1. Output MUST be a single, valid JSON object.
    2. Keys are the NEW canonical terms (e.g., "FOUNDED").
    3. Values are a list of the original English terms that belong to that group.
    4. Every single term from the input list MUST be included in one of the groups.
    English Terms: {json.dumps(english_terms)}
    """
    tqdm.write("Sending unique English terms to AI for consolidation...")
    consolidation_map = call_generative_model(prompt, model)
    print("Stage 2 Complete. Received consolidation map.")
    return consolidation_map

# --- Main Orchestration ---
def run_two_stage_refinement():
    farsi_relations = get_unique_farsi_relations(SOURCE_JSON_PATH)
    if not farsi_relations: return

    model = genai.GenerativeModel('gemini-1.5-pro-latest')

    # Stage 1
    draft_map = generate_draft_map(farsi_relations, model)
    if not draft_map:
        print("Failed to generate draft map. Aborting.")
        return
    with open(DRAFT_MAP_PATH, 'w', encoding='utf-8') as f:
        json.dump(draft_map, f, ensure_ascii=False, indent=2)
    print(f"Intermediate draft map saved to {DRAFT_MAP_PATH}")

    # Stage 2
    unique_english_terms = sorted(list(set(draft_map.values())))
    consolidation_map = consolidate_english_terms(unique_english_terms, model)
    if not consolidation_map:
        print("Failed to generate consolidation map. Aborting.")
        return

    # Stage 3: Final Assembly
    print("\n--- Stage 3: Assembling Final Standardized Map ---")
    final_map = {}
    # Create a reverse map for easy lookup: {original_english: canonical_english}
    reverse_consolidation_map = {}
    for canonical, originals in consolidation_map.items():
        for original in originals:
            reverse_consolidation_map[original] = canonical
            
    for farsi_term, draft_english_term in draft_map.items():
        final_map[farsi_term] = reverse_consolidation_map.get(draft_english_term, draft_english_term)
    
    print("Final assembly complete.")
    
    # Final Verification
    missing_relations = set(farsi_relations) - set(final_map.keys())
    if not missing_relations:
        print("Verification successful: All original Farsi relations are present in the final map.")
    else:
        print(f"WARNING: {len(missing_relations)} Farsi relations were lost during final assembly.")

    with open(FINAL_MAP_PATH, 'w', encoding='utf-8') as f:
        json.dump(final_map, f, ensure_ascii=False, indent=2)
    print(f"Process complete. Final standardized map saved to {FINAL_MAP_PATH}")

if __name__ == "__main__":
    run_two_stage_refinement()