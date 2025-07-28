import json
import os
import re
import time
from dotenv import load_dotenv
import google.generativeai as genai
from tqdm import tqdm

# --- Configuration ---
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SUGGESTED_MAP_PATH = os.path.join(PROJECT_ROOT, 'data', 'suggested_schema_map.json')
CURATED_MAP_PATH = os.path.join(PROJECT_ROOT, 'data', 'curated_schema_map.json')
BATCH_SIZE = 100 # Process 100 terms per API call

# --- Helper Functions ---
def load_json(path, default_value):
    if not os.path.exists(path):
        print(f"ERROR: File not found at {path}")
        return default_value
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"ERROR: Could not read or parse {path}: {e}")
        return default_value

def save_json(data, path):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def call_generative_model(prompt, model):
    max_retries = 3
    for i in range(max_retries):
        try:
            response = model.generate_content(prompt)
            cleaned_response = response.text.strip().replace("```json", "").replace("```", "")
            return json.loads(cleaned_response)
        except Exception as e:
            tqdm.write(f"  - API call attempt {i+1} failed. Error: {e}. Retrying...")
            time.sleep(2)
    tqdm.write("  - FAILED to get valid JSON after multiple retries.")
    return None

# --- Curation Logic ---
def stage_one_local_curation(suggested_map):
    """Applies local rules to perform an initial curation pass."""
    print("--- Stage 1: Applying Local Curation Rules ---")
    initial_curated_map = {}
    terms_needing_verbs = {}
    bad_categories = {"EVENT", "LEGAL", "SOCIAL", "LEADERSHIP", "FAMILY", "WORK", "POLITICAL", "JUDICIAL", "COMMUNICATION", "EDUCATION"}

    for farsi_term, original_english in tqdm(suggested_map.items(), desc="Stage 1 Curation"):
        if original_english in bad_categories:
            terms_needing_verbs[farsi_term] = original_english
            initial_curated_map[farsi_term] = f"PLACEHOLDER_FOR_{farsi_term.upper()}"
            continue

        curated_term = original_english.upper().replace(" ", "_")
        if farsi_term.endswith(("_شد", "_یافت", "_دیدند")) or "دید_از" in farsi_term:
            if not curated_term.startswith("WAS_"):
                curated_term = f"WAS_{curated_term}"
        
        if curated_term.startswith("WAS_WAS_"):
            curated_term = curated_term[4:]
            
        initial_curated_map[farsi_term] = curated_term
        
    print(f"Stage 1 complete. Flagged {len(terms_needing_verbs)} terms for AI verb generation.")
    return initial_curated_map, terms_needing_verbs

def stage_two_ai_verb_generation(terms_to_fix, model):
    """Uses the AI to generate specific verbs for the flagged terms IN BATCHES."""
    print("\n--- Stage 2: AI Verb Generation for Flagged Terms (in Batches) ---")
    if not terms_to_fix:
        print("No terms needed AI verb generation. Skipping.")
        return {}

    farsi_terms_list = list(terms_to_fix.keys())
    final_verbs_map = {}
    
    # --- CORRECTED LOGIC: Create batches from the list of terms that need fixing ---
    batches = [farsi_terms_list[i:i + BATCH_SIZE] for i in range(0, len(farsi_terms_list), BATCH_SIZE)]
    
    for batch in tqdm(batches, desc="Stage 2: AI Verb Gen"):
        prompt = f"""
        You are a linguist and data architect. Your task is to provide a concise, specific, active English verb in UPPER_SNAKE_CASE for each of the following Farsi terms.
        
        RULES:
        1. Your output MUST be a single, valid JSON object.
        2. The keys of the JSON object must be the original Farsi terms.
        3. The values must be the English verb you generate.
        4. Focus on the ACTION. For example, for "ابراز_ندامت" (expression of regret), the verb is "EXPRESSED_REMORSE". For "آمر" (commander), the verb is "ORDERED".
        
        Here is the list of Farsi terms to process for this batch:
        {json.dumps(batch, ensure_ascii=False)}

        Produce ONLY the JSON object as your response.
        """
        
        batch_map = call_generative_model(prompt, model)
        if batch_map:
            final_verbs_map.update(batch_map)
        time.sleep(1) # Be a good citizen and rate-limit our calls

    if final_verbs_map:
        print(f"Stage 2 complete. Received {len(final_verbs_map)} verb suggestions from the AI.")
    else:
        print("Stage 2 failed. Could not get verb suggestions from the AI.")
    
    return final_verbs_map

def bulk_curate_v2():
    """Main function for the three-stage automated curation process."""
    suggested_map = load_json(SUGGESTED_MAP_PATH, None)
    if suggested_map is None: return

    model = genai.GenerativeModel('gemini-1.5-pro-latest')

    # Stage 1
    initial_map, terms_to_fix = stage_one_local_curation(suggested_map)

    # Stage 2
    ai_generated_verbs = stage_two_ai_verb_generation(terms_to_fix, model)

    # Stage 3: Final Assembly
    print("\n--- Stage 3: Assembling Final Curated Map ---")
    final_map = initial_map.copy()
    fixed_count = 0
    unfixed_count = 0
    for farsi_term, placeholder in final_map.items():
        if "PLACEHOLDER_FOR_" in placeholder:
            if farsi_term in ai_generated_verbs:
                final_map[farsi_term] = ai_generated_verbs[farsi_term]
                fixed_count += 1
            else:
                unfixed_count += 1
            
    print(f"Stage 3 complete. Merged {fixed_count} AI-generated verbs into the final map.")
    if unfixed_count > 0:
        print(f"WARNING: {unfixed_count} terms could not be fixed by the AI and remain as placeholders.")

    save_json(final_map, CURATED_MAP_PATH)
    print(f"\nProcess complete. New curated map saved to: {CURATED_MAP_PATH}")
    print("Please give the new file a final, quick review for any remaining issues or placeholders.")

if __name__ == "__main__":
    bulk_curate_v2()