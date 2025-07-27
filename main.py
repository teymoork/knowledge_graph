import os
import sys
import json
from datetime import datetime
from typing import Any, List, Tuple, Dict, Union
import google.generativeai as genai
from tqdm import tqdm
import subprocess

# --- Path Correction ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

import config
from graph_schema import NodeLabel, RelationshipLabel

# --- Constants ---
BOOK_PATH = os.path.join("data", "book.txt")
GRAPH_OUTPUT_PATH = os.path.join("data", "extracted_graph.json")
STATS_PATH = os.path.join("data", "progress_stats.json")
CHUNK_SIZE = 10000
CHUNK_OVERLAP = 500

# --- Core Extraction Logic ---

def read_book_chunks(file_path: str, chunk_size: int, overlap: int) -> List[str]:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
    except FileNotFoundError:
        print(f"ERROR: The file {file_path} was not found.")
        return []
    except UnicodeDecodeError:
        print(f"ERROR: Failed to decode the file at {file_path} with UTF-8 encoding.")
        return []
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks

def load_data(file_path: str, default_value: Union[List, Dict]) -> Union[List, Dict]:
    if not os.path.exists(file_path):
        return default_value
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if file_path == GRAPH_OUTPUT_PATH and isinstance(data, dict) and "graph" in data:
                return data["graph"]
            return data
    except (json.JSONDecodeError, IOError) as e:
        print(f"WARNING: Could not read or parse {file_path}: {e}. Starting with default.")
        return default_value

def save_data(data: Union[List, Dict], file_path: str) -> None:
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            if file_path == GRAPH_OUTPUT_PATH:
                json.dump({"graph": data}, f, ensure_ascii=False, indent=2)
            else:
                json.dump(data, f, ensure_ascii=False, indent=2)
    except IOError as e:
        print(f"ERROR: Failed to save data to {file_path}: {e}")

def generate_system_prompt() -> str:
    node_labels_str = ", ".join([f"`{label.value}`" for label in NodeLabel])
    relationship_types_str = ", ".join([f"`{rel.value}`" for rel in RelationshipLabel])
    return f"""
شما یک مورخ و تحلیلگر داده متخصص هستید. وظیفه شما خواندن متن تاریخی فارسی زیر و استخراج دقیق موجودیت‌ها و روابط بین آنها بر اساس یک اسکیمای مشخص است.
**اسکیما (Schema):**
1.  **برچسب‌های موجودیت مجاز:** {node_labels_str}
2.  **انواع روابط مجاز:** {relationship_types_str}
**دستورالعمل خروجی:**
- خروجی شما باید **فقط** یک آبجکت JSON معتبر با یک کلید به نام `graph` باشد که مقدار آن یک لیست از سه‌تایی‌ها است.
- هر سه‌تایی باید یک آبجکت با سه کلید باشد: `head`, `relation`, `tail`.
**مثال برای خروجی JSON:**
{{
  "graph": [
    {{ "head": "کوروش بزرگ", "relation": "حکومت_کرد_در", "tail": "ایران" }}
  ]
}}
قوانین مهم:
هرگز از اسکیمای تعریف نشده استفاده نکنید.
اگر هیچ رابطه‌ای پیدا نکردید، یک لیست خالی برگردانید: {{"graph": []}}.
"""

def process_chunks(model: Any, chunks_to_process: List[Tuple[int, str]], system_prompt: str) -> Tuple[List[Dict], List[int], List[int]]:
    newly_extracted_triplets = []
    successfully_processed_indices = []
    failed_indices = []
    for index, chunk_text in tqdm(chunks_to_process, desc="Extracting from chunks"):
        try:
            full_prompt = f"{system_prompt}\n\n**متن ورودی برای تحلیل:**\n\n---\n{chunk_text}\n---"
            response = model.generate_content(full_prompt)
            response_text = response.text.strip().replace("```json", "").replace("```", "")
            data = json.loads(response_text)
            
            if isinstance(data, dict) and "graph" in data and isinstance(data["graph"], list):
                chunk_triplets = data["graph"]
                newly_extracted_triplets.extend(chunk_triplets)
                successfully_processed_indices.append(index)
                tqdm.write(f"Chunk {index}: Extracted {len(chunk_triplets)} triplets.")
            else:
                tqdm.write(f"WARNING: Chunk {index}: Received malformed data from API.")
                failed_indices.append(index)
        except json.JSONDecodeError as e:
            tqdm.write(f"WARNING: Chunk {index}: Failed to decode JSON from API response: {e}")
            failed_indices.append(index)
        except Exception as e:
            tqdm.write(f"ERROR: An error occurred during API call for chunk {index}: {e}")
            failed_indices.append(index)
    return newly_extracted_triplets, successfully_processed_indices, failed_indices

# --- Menu Functions ---

def run_script(script_path: str) -> None:
    try:
        result = subprocess.run(["poetry", "run", "python", script_path], check=True, capture_output=True, text=True)
        print(f"Successfully ran '{script_path}'.")
    except FileNotFoundError:
        print(f"ERROR: Poetry or script '{script_path}' not found. Ensure Poetry is installed and the script exists.")
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to run '{script_path}': {e}\nOutput: {e.output}")

def display_status(stats: Dict[str, Any]) -> None:
    total_chunks = stats.get("total_chunks_in_book", 0)
    processed_count = len(stats.get("processed_chunks", []))
    failed_chunks = stats.get("failed_chunks", [])
    failed_count = len(failed_chunks)
    percentage = (processed_count / total_chunks * 100) if total_chunks > 0 else 0
    print("\n--- Progress Status ---")
    print(f"Processed {processed_count} out of {total_chunks} chunks ({percentage:.2f}% complete).")
    print(f"Total triplets extracted so far: {stats.get('total_triplets_extracted', 0)}")
    print(f"Number of failed chunks: {failed_count}")
    if failed_count > 0:
        print(f"Failed chunk IDs: {failed_chunks}")
    print(f"Last updated: {stats.get('last_updated', 'Never')}")
    print("-----------------------\n")

def extraction_menu() -> None:
    print("\n--- Extraction Sub-Menu ---")
    # Load all data at the start of the menu
    try:
        genai.configure(api_key=config.GOOGLE_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-pro-latest')
        book_chunks = read_book_chunks(BOOK_PATH, CHUNK_SIZE, CHUNK_OVERLAP)
        total_chunks = len(book_chunks)
        print(f"Book loaded: {total_chunks} chunks found.")
    except Exception as e:
        print(f"FATAL ERROR: Could not initialize Gemini or read book: {e}")
        return

    while True:
        print("1. Enter a chunk range (e.g., '0-9')")
        print("2. Extract all remaining chunks")
        print("3. Retry failed chunks")
        print("4. Print status")
        choice = input("Your choice (Press Enter to return to main menu): ").strip()

        if choice == "":
            break
        
        # Reload data on every loop to ensure it's fresh
        stats = load_data(STATS_PATH, default_value={})
        stats["total_chunks_in_book"] = total_chunks
        all_triplets = load_data(GRAPH_OUTPUT_PATH, default_value=[])
        processed_chunks_set = set(stats.get("processed_chunks", []))
        failed_chunks_set = set(stats.get("failed_chunks", []))

        chunks_to_process_indices = []
        
        if choice == '1':
            range_input = input("Enter chunk range (e.g., '0-9'): ").strip()
            try:
                start_str, end_str = range_input.split('-')
                start_chunk, end_chunk = int(start_str), int(end_str) + 1
                if not (0 <= start_chunk < end_chunk <= total_chunks):
                    print(f"ERROR: Invalid range. Must be between 0 and {total_chunks - 1}.")
                    continue
                chunks_to_process_indices = [i for i in range(start_chunk, end_chunk) if i not in processed_chunks_set]
            except ValueError:
                print("ERROR: Invalid format. Please use 'start-end' (e.g., '0-9').")
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
            print("ERROR: Invalid choice.")
            continue

        if not chunks_to_process_indices:
            print("No new chunks to process for the selected option.")
            continue
        
        print(f"Found {len(chunks_to_process_indices)} chunks to process.")
        chunks_with_indices = [(i, book_chunks[i]) for i in chunks_to_process_indices]
        system_prompt = generate_system_prompt()
        new_triplets, successful_indices, newly_failed_indices = process_chunks(model, chunks_with_indices, system_prompt)
        
        processed_chunks_set.update(successful_indices)
        failed_chunks_set.difference_update(successful_indices)
        failed_chunks_set.update(newly_failed_indices)

        if new_triplets:
            all_triplets.extend(new_triplets)
        
        stats["processed_chunks"] = sorted(list(processed_chunks_set))
        stats["failed_chunks"] = sorted(list(failed_chunks_set))
        stats["total_triplets_extracted"] = len(all_triplets)
        stats["last_updated"] = datetime.now().isoformat()
        
        save_data(all_triplets, GRAPH_OUTPUT_PATH)
        save_data(stats, STATS_PATH)
        
        print(f"\nRun complete. Added {len(new_triplets)} new triplets.")
        display_status(stats)

def main_menu() -> None:
    while True:
        print("\n=============================================")
        print(" Farsi History Knowledge Graph ")
        print("=============================================")
        print("1. Extract Triplets from Text")
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
            run_script("qa_interface.py")
        elif choice == '4':
            run_script("discover_schema.py")
        elif choice in ['quit', 'q']:
            print("Exiting project interface. Goodbye!")
            break
        else:
            print("ERROR: Invalid choice, please try again.")

if __name__ == "__main__":
    main_menu()