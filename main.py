import os
import sys
import json
from datetime import datetime
import google.generativeai as genai
from tqdm import tqdm
import subprocess

# --- Path Correction ---
# This part seems specific to your environment, so we'll keep it.
# If 'src' is in the same directory, this might not be needed when running as a module.
# However, to be safe, we will retain it.
sys.path.append(os.path.dirname(__file__))
# --- End Path Correction ---

# config.py is not a file we've created together. 
# I will assume GOOGLE_API_KEY is loaded from .env as in our other scripts.
from dotenv import load_dotenv
load_dotenv()

# ==============================================================================
# --- MODIFICATION START ---
# We are replacing the old Enum-based schema import with our new, official schema.
# The old lines were:
# from src.graph_schema import NodeLabel, RelationshipLabel
#
# The new lines are:
from src.graph_schema import BASE_NODE_LABELS, RELATIONSHIP_TYPES
# --- MODIFICATION END ---
# ==============================================================================


# --- Constants ---
# Using paths relative to the project root is generally more robust.
# Assuming this script is run from the project root.
DATA_DIR = "data"
BOOK_PATH = os.path.join(DATA_DIR, "book.txt")
GRAPH_OUTPUT_PATH = os.path.join(DATA_DIR, "extracted_graph.json")
STATS_PATH = os.path.join(DATA_DIR, "progress_stats.json")
CHUNK_SIZE = 10000
CHUNK_OVERLAP = 500

# --- Core Extraction Logic ---

def read_book_chunks(file_path: str, chunk_size: int, overlap: int) -> list[str]:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
    except FileNotFoundError:
        print(f"Error: The file {file_path} was not found.")
        return []
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks

def load_data(file_path: str, default_value):
    if not os.path.exists(file_path):
        return default_value
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return default_value

def save_data(data: any, file_path: str):
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except IOError as e:
        print(f"Error saving data to {file_path}: {e}")

def generate_system_prompt() -> str:
    # ==============================================================================
    # --- MODIFICATION START ---
    # We now build the prompt strings from our new lists in graph_schema.py
    node_labels_str = ", ".join([f'"{label}"' for label in BASE_NODE_LABELS])
    relationship_types_str = ",\n".join([f'    "{rel}"' for rel in RELATIONSHIP_TYPES])
    
    # The prompt is updated to reflect the new schema source and instructions.
    return f"""
You are a meticulous historian and data analyst. Your task is to extract structured information from a Farsi historical text.

# Instructions:
1.  Your output MUST be a single valid JSON object with one key: "graph".
2.  The "graph" key must contain a list of objects. Each object represents a relationship.
3.  Each relationship object MUST have the following keys: "head", "head_label", "relation", "tail", "tail_label", and "properties".
4.  The "head_label" and "tail_label" MUST be one of the following allowed node labels:
    [{node_labels_str}]
5.  The "relation" MUST be one of the following predefined English relationship types. Do NOT use Farsi or invent new types.
    [
    {relationship_types_str}
    ]
6.  The "properties" key must be a JSON object. It can be empty (`{{}}`) if no specific properties are found.
7.  If no relationships are found, return an empty list inside the "graph" key: `{{"graph": []}}`

# Example JSON Output:
```json
{{
  "graph": [
    {{
      "head": "شخص الف",
      "head_label": "Person",
      "relation": "SUPPORTED",
      "tail": "سازمان ب",
      "tail_label": "Organization",
      "properties": {{
        "visibility": "secret",
        "type": "financial"
      }}
    }}
  ]
}}
"""
    # --- MODIFICATION END ---
    # ==============================================================================

def process_chunks(model, chunks_to_process: list[tuple[int, str]], system_prompt: str) -> tuple[list, list[int], list[int], int, int]:
    newly_extracted_relationships = []
    successfully_processed_indices = []
    failed_indices = []
    total_input_tokens = 0
    total_output_tokens = 0
    for index, chunk_text in tqdm(chunks_to_process, desc="Extracting from chunks"):
        try:
            full_prompt = f"{system_prompt}\n\n**متن ورودی برای تحلیل:**\n\n---\n{chunk_text}\n---"
            
            input_token_count = model.count_tokens(full_prompt).total_tokens
            total_input_tokens += input_token_count
            
            response = model.generate_content(full_prompt)
            
            usage_metadata = response.usage_metadata
            if usage_metadata:
                total_output_tokens += usage_metadata.candidates_token_count
            
            response_text = response.text.strip().replace("```json", "").replace("```", "")
            data = json.loads(response_text)
            
            if "graph" in data and isinstance(data["graph"], list):
                chunk_relationships = data["graph"]
                newly_extracted_relationships.extend(chunk_relationships)
                successfully_processed_indices.append(index)
                tqdm.write(f"Chunk {index}: Extracted {len(chunk_relationships)} relationships. Input Tokens: {input_token_count}")
            else:
                tqdm.write(f"Warning: Chunk {index}: Received malformed data from API.")
                failed_indices.append(index)
        except (json.JSONDecodeError, Exception) as e:
            tqdm.write(f"Warning: Chunk {index}: An error occurred. Details: {e}")
            failed_indices.append(index)
            
    return newly_extracted_relationships, successfully_processed_indices, failed_indices, total_input_tokens, total_output_tokens

def run_script(script_path: str):
    # Using sys.executable ensures we use the python from the current virtual env
    try:
        subprocess.run([sys.executable, script_path], check=True)
    except (FileNotFoundError, subprocess.CalledProcessError) as e:
        print(f"\nError running '{script_path}': {e}")

def display_status(stats: dict):
    total_chunks = stats.get("total_chunks_in_book", 0)
    processed_count = len(stats.get("processed_chunks", []))
    failed_chunks = stats.get("failed_chunks", [])
    failed_count = len(failed_chunks)
    percentage = (processed_count / total_chunks * 100) if total_chunks > 0 else 0
    print("\n--- Progress Status ---")
    print(f"Processed {processed_count} out of {total_chunks} chunks ({percentage:.2f}% complete).")
    print(f"Total relationships extracted so far: {stats.get('total_relationships_extracted', 0)}")
    print(f"Number of failed chunks: {failed_count}")
    if failed_count > 0:
        print(f"Failed chunk IDs: {failed_chunks}")
    print("\n--- Token Usage ---")
    print(f"Total Input Tokens Processed: {stats.get('total_input_tokens', 0):,}")
    print(f"Total Output Tokens Generated: {stats.get('total_output_tokens', 0):,}")
    print(f"Last updated: {stats.get('last_updated', 'Never')}")
    print("-----------------------\n")

def extraction_menu():
    print("\n--- Extraction Sub-Menu ---")
    try:
        # Using the .env loaded key
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        model = genai.GenerativeModel('gemini-1.5-pro-latest')
        book_chunks = read_book_chunks(BOOK_PATH, CHUNK_SIZE, CHUNK_OVERLAP)
        total_chunks = len(book_chunks)
        print(f"Book loaded: {total_chunks} chunks found.")
    except Exception as e:
        print(f"FATAL ERROR: Could not initialize Gemini or read book. Details: {e}")
        return

    while True:
        print("1. Enter a chunk range (e.g., '0-9')")
        print("2. Extract all remaining chunks")
        print("3. Retry failed chunks")
        print("4. Print status")
        choice = input("Your choice (Press Enter to return to main menu): ").strip()

        if choice == "":
            break
        
        stats = load_data(STATS_PATH, default_value={})
        stats["total_chunks_in_book"] = total_chunks
        graph_data = load_data(GRAPH_OUTPUT_PATH, default_value={"graph": []})
        if "graph" not in graph_data or not isinstance(graph_data["graph"], list):
            graph_data = {"graph": []}
        processed_chunks_set = set(stats.get("processed_chunks", []))
        failed_chunks_set = set(stats.get("failed_chunks", []))

        chunks_to_process_indices = []
        
        if choice == '1':
            range_input = input("Enter chunk range (e.g., '0-9'): ").strip()
            try:
                start_str, end_str = range_input.split('-')
                start_chunk, end_chunk = int(start_str), int(end_str) + 1
                if not (0 <= start_chunk < end_chunk <= total_chunks):
                    print(f"Error: Invalid range.")
                    continue
                chunks_to_process_indices = [i for i in range(start_chunk, end_chunk) if i not in processed_chunks_set]
            except ValueError:
                print("Error: Invalid format.")
                continue
        elif choice == '2':
            chunks_to_process_indices = [i for i in range(total_chunks) if i not in processed_chunks_set]
        elif choice == '3':
            if not failed_chunks_set:
                print("No failed chunks to retry.")
                continue
            chunks_to_process_indices = sorted(list(failed_chunks_set))
        elif choice == '4':
            display_status(stats)
            continue
        else:
            print("Invalid choice.")
            continue

        if not chunks_to_process_indices:
            print("No new chunks to process for the selected option.")
            continue
        
        print(f"Found {len(chunks_to_process_indices)} chunks to process.")
        chunks_with_indices = [(i, book_chunks[i]) for i in chunks_to_process_indices]
        system_prompt = generate_system_prompt()
        new_relationships, successful_indices, newly_failed_indices, input_tokens, output_tokens = process_chunks(model, chunks_with_indices, system_prompt)
        
        processed_chunks_set.update(successful_indices)
        failed_chunks_set.difference_update(successful_indices)
        failed_chunks_set.update(newly_failed_indices)

        if new_relationships:
            graph_data["graph"].extend(new_relationships)
        
        stats["processed_chunks"] = sorted(list(processed_chunks_set))
        stats["failed_chunks"] = sorted(list(failed_chunks_set))
        stats["total_relationships_extracted"] = len(graph_data["graph"])
        stats["last_updated"] = datetime.now().isoformat()
        stats["total_input_tokens"] = stats.get("total_input_tokens", 0) + input_tokens
        stats["total_output_tokens"] = stats.get("total_output_tokens", 0) + output_tokens
        
        save_data(graph_data, GRAPH_OUTPUT_PATH)
        save_data(stats, STATS_PATH)
        
        print(f"\nRun complete. Added {len(new_relationships)} new relationships.")
        display_status(stats)

def main_menu():
    while True:
        print("\n=============================================")
        print(" Farsi History Knowledge Graph ")
        print("=============================================")
        print("1. Extract Relationships from Text")
        print("2. Populate Neo4j Database")
        print("3. Ask Questions (QA Interface)")
        print("4. Discover Schema (AI Suggestions)")
        print("\nEnter 'quit' or 'q' to exit.")
        choice = input("\nPlease enter your choice: ").lower().strip()

        if choice == '1':
            extraction_menu()
        elif choice == '2':
            run_script("src/populate.py")
        elif choice == '3':
            # Assuming these scripts are in the root, not src/
            run_script("qa_interface.py")
        elif choice == '4':
            run_script("discover_schema.py")
        elif choice in ['quit', 'q']:
            print("Exiting project interface. Goodbye!")
            break
        else:
            print("Invalid choice, please try again.")

if __name__ == "__main__":
    main_menu()