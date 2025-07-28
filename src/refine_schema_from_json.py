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

SOURCE_JSON_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'extracted_graph.json.250728.full')
OUTPUT_MAP_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'suggested_schema_map.json')
BATCH_SIZE = 100 # Process 100 relationship types per API call

def get_unique_farsi_relations(file_path):
    """Scans the large JSON file to find all unique Farsi relationship types."""
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
    except FileNotFoundError:
        print(f"ERROR: Source file not found at {file_path}")
        return None
    except Exception as e:
        print(f"An error occurred while reading the JSON file: {e}")
        return None

def get_ai_standardization_for_batch(batch, model):
    """
    Sends a single batch to the Gemini API for standardization,
    now including the self-correction loop.
    """
    farsi_list_str = "\n".join([f"- {rel}" for rel in batch])
    
    initial_prompt = f"""
    You are a data architect specializing in knowledge graphs. Your task is to translate and standardize a list of Farsi relationship types into a clean, consistent set of English relationship types.

    RULES:
    1. The output MUST be a single, valid JSON object.
    2. The keys are the original Farsi types; the values are the proposed English translations in UPPER_SNAKE_CASE.
    3. Merge semantically similar concepts into a single canonical English term (e.g., map both "تاسیس کرد" and "بنیان نهاد" to "FOUNDED").
    4. Ensure all strings in the JSON output are correctly escaped.
    5. Produce ONLY the JSON object in your response.

    Here is the list of Farsi relationship types to process:
    {farsi_list_str}
    """
    
    current_prompt = initial_prompt
    max_retries = 3
    for i in range(max_retries):
        try:
            response = model.generate_content(current_prompt)
            cleaned_response = response.text.strip().replace("```json", "").replace("```", "")
            return json.loads(cleaned_response)
        except json.JSONDecodeError as e:
            tqdm.write(f"  - Attempt {i+1} failed for batch. Error: {e}. Retrying with self-correction...")
            # Create the self-correction prompt
            current_prompt = f"""
            Your previous response for a batch resulted in a JSON parsing error.
            Please fix the following text to make it a single, valid JSON object.
            Do not apologize or explain, just provide the corrected JSON.

            ERROR: {e}

            FAULTY TEXT:
            ---
            {response.text}
            ---
            
            Correct the faulty text and provide only the valid JSON object.
            """
            time.sleep(2)
        except Exception as e:
            tqdm.write(f"  - An unexpected error occurred in batch processing: {e}. Retrying...")
            time.sleep(2)

    tqdm.write(f"  - FAILED to process batch after {max_retries} retries.")
    return {} # Return empty dict on failure

def refine_schema_in_batches():
    """
    Main function to orchestrate the schema refinement process in manageable batches.
    """
    farsi_relations = get_unique_farsi_relations(SOURCE_JSON_PATH)
    if not farsi_relations:
        return

    model = genai.GenerativeModel('gemini-1.5-pro-latest')
    final_schema_map = {}
    
    # Create batches from the full list
    batches = [farsi_relations[i:i + BATCH_SIZE] for i in range(0, len(farsi_relations), BATCH_SIZE)]
    print(f"\nDivided relationship types into {len(batches)} batches of up to {BATCH_SIZE} each.")

    for i, batch in enumerate(tqdm(batches, desc="Processing batches")):
        tqdm.write(f"Processing batch {i+1}/{len(batches)}...")
        batch_map = get_ai_standardization_for_batch(batch, model)
        final_schema_map.update(batch_map)
        tqdm.write(f"  - Received {len(batch_map)} mappings from batch. Total mappings so far: {len(final_schema_map)}")
        time.sleep(1) # Rate limit to be safe

    print(f"\nCompleted all batches. Total unique mappings generated: {len(final_schema_map)}")
    
    # Verification step
    missing_relations = set(farsi_relations) - set(final_schema_map.keys())
    if missing_relations:
        print(f"\nWARNING: {len(missing_relations)} Farsi relations were not mapped by the AI.")
        print("First 5 missing relations:", list(missing_relations)[:5])
    else:
        print("\nVerification successful: All Farsi relations have been mapped.")

    print(f"\nSaving complete schema map to {OUTPUT_MAP_PATH}")
    with open(OUTPUT_MAP_PATH, 'w', encoding='utf-8') as f:
        json.dump(final_schema_map, f, ensure_ascii=False, indent=2)
    print("Save complete.")

if __name__ == "__main__":
    refine_schema_in_batches()