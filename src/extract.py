import os
import json
import sys
from datetime import datetime
from typing import Any, List, Tuple, Dict, Union
import google.generativeai as genai
from tqdm import tqdm
import config
from graph_schema import NodeLabel, RelationshipLabel

# --- File Paths ---
BOOK_PATH = os.path.join("data", "book.txt")
GRAPH_OUTPUT_PATH = os.path.join("data", "extracted_graph.json")
STATS_PATH = os.path.join("data", "progress_stats.json")

# --- Processing Parameters ---
CHUNK_SIZE = 10000
CHUNK_OVERLAP = 500

def generate_system_prompt() -> str:
    node_labels_str = ", ".join([f"`{label.value}`" for label in NodeLabel])
    relationship_types_str = ", ".join([f"`{rel.value}`" for rel in RelationshipLabel])
    
    return f"""
شما یک مورخ و تحلیلگر داده متخصص هستید. وظیفه شما خواندن متن تاریخی فارسی زیر و استخراج دقیق موجودیت‌ها و روابط بین آنها بر اساس یک اسکیمای مشخص است.

**اسکیما (Schema):**
شما باید فقط و فقط از برچسب‌های موجودیت (Node Labels) و انواع روابط (Relationship Types) زیر استفاده کنید:

1.  **برچسب‌های موجودیت مجاز:**
    {node_labels_str}

2.  **انواع روابط مجاز:**
    {relationship_types_str}

**دستورالعمل خروجی:**
- خروجی شما باید **فقط** یک آبجکت JSON معتبر باشد.
- این آبجکت JSON باید تنها یک کلید به نام `graph` داشته باشد.
- مقدار کلید `graph` باید یک لیست (Array) از سه‌تایی‌ها (triplets) باشد.
- هر سه‌تایی در لیست باید یک آبجکت با سه کلید باشد: `head`, `relation`, `tail`.
- `head` و `tail` نام کامل موجودیت‌های استخراج شده هستند.
- `relation` باید دقیقاً یکی از انواع روابط مجاز باشد.

**مثال برای خروجی JSON:**
{{
  "graph": [
    {{
      "head": "کوروش بزرگ",
      "relation": "حکومت_کرد_در",
      "tail": "ایران"
    }},
    {{
      "head": "داریوش بزرگ",
      "relation": "جانشین_شد",
      "tail": "کمبوجیه دوم"
    }}
  ]
}}

قوانین مهم:
هرگز موجودیت یا رابطه‌ای را که در اسکیمای بالا تعریف نشده است، استخراج نکنید.
اگر هیچ رابطه معتبری در متن پیدا نکردید، یک لیست خالی برای کلید graph برگردانید: {{"graph": []}}.
نام کامل و دقیق موجودیت‌ها را همانطور که در متن آمده است استخراج کنید.
به متن ورودی که در ادامه می‌آید به دقت توجه کنید و استخراج را فقط بر اساس آن انجام دهید.
"""

def read_book_chunks(file_path: str, chunk_size: int, overlap: int) -> List[str]:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
    except FileNotFoundError:
        print(f"ERROR: The file {file_path} was not found.")
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

def process_chunks(model, chunks_to_process: List[Tuple[int, str]], system_prompt: str) -> Tuple[List[Dict], List[int], List[int]]:
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
        except json.JSONDecodeError:
            tqdm.write(f"WARNING: Chunk {index}: Failed to decode JSON from API response.")
            failed_indices.append(index)
        except Exception as e:
            tqdm.write(f"ERROR: An error occurred during API call for chunk {index}: {e}")
            failed_indices.append(index)
    return newly_extracted_triplets, successfully_processed_indices, failed_indices

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

def main() -> None:
    print("--- Interactive Knowledge Graph Extraction ---")
    
    try:
        genai.configure(api_key=config.GOOGLE_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-pro-latest')
        print("Google Gemini API configured successfully.")
    except Exception as e:
        print(f"ERROR: Failed to configure Gemini API: {e}")
        return

    book_chunks = read_book_chunks(BOOK_PATH, CHUNK_SIZE, CHUNK_OVERLAP)
    if not book_chunks:
        print("No content to process. Exiting.")
        return

    total_chunks = len(book_chunks)
    print(f"Book split into {total_chunks} chunks.")

    stats = load_data(STATS_PATH, default_value={})
    stats["total_chunks_in_book"] = total_chunks

    all_triplets = load_data(GRAPH_OUTPUT_PATH, default_value=[])

    processed_chunks_set = set(stats.get("processed_chunks", []))
    failed_chunks_set = set(stats.get("failed_chunks", []))

    while True:
        user_input = input(
            "Enter a chunk range (e.g., '0-9'), 'all', 'retry', 'status', or 'quit': "
        ).lower().strip()

        if user_input in ['quit', 'exit']:
            print("Exiting.")
            break
        
        if user_input == 'status':
            display_status(stats)
            continue

        chunks_to_process_indices = []
        if user_input == 'retry':
            if not failed_chunks_set:
                print("No failed chunks to retry.")
                continue
            chunks_to_process_indices = sorted(list(failed_chunks_set))
            print(f"Retrying {len(chunks_to_process_indices)} failed chunks...")
        elif user_input == 'all':
            chunks_to_process_indices = [i for i in range(total_chunks) if i not in processed_chunks_set]
        elif '-' in user_input:
            try:
                start_str, end_str = user_input.split('-')
                start_chunk = int(start_str)
                end_chunk = int(end_str) + 1
                if not (0 <= start_chunk < end_chunk <= total_chunks):
                    print(f"ERROR: Invalid range. Must be between 0 and {total_chunks - 1}.")
                    continue
                chunks_to_process_indices = [i for i in range(start_chunk, end_chunk) if i not in processed_chunks_set]
            except ValueError:
                print("ERROR: Invalid format. Please use 'start-end' (e.g., '0-9').")
                continue
        else:
            print("ERROR: Invalid command.")
            continue

        if not chunks_to_process_indices:
            print("All chunks in the specified range have already been processed.")
            continue
            
        print(f"Found {len(chunks_to_process_indices)} new chunks to process.")
        
        chunks_with_indices = [(i, book_chunks[i]) for i in chunks_to_process_indices]
        
        system_prompt = generate_system_prompt()
        new_triplets, successful_indices, newly_failed_indices = process_chunks(model, chunks_with_indices, system_prompt)
        
        # Update sets based on results
        processed_chunks_set.update(successful_indices)
        failed_chunks_set.difference_update(successful_indices)  # Remove successful ones from failed set
        failed_chunks_set.update(newly_failed_indices)  # Add any new failures

        if new_triplets:
            all_triplets.extend(new_triplets)
        
        # Update stats dictionary
        stats["processed_chunks"] = sorted(list(processed_chunks_set))
        stats["failed_chunks"] = sorted(list(failed_chunks_set))
        stats["total_triplets_extracted"] = len(all_triplets)
        stats["last_updated"] = datetime.now().isoformat()
        
        # Save everything
        save_data(all_triplets, GRAPH_OUTPUT_PATH)
        save_data(stats, STATS_PATH)
        
        print(f"\nRun complete. Added {len(new_triplets)} new triplets.")
        display_status(stats)

if __name__ == "__main__":
    main()