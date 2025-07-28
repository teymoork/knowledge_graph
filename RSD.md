# System Design Document: Farsi History Knowledge Graph

**Version:** 2.0
**Date:** July 28, 2024
**Author:** Teymoor Kh, assisted by Gemini 2.5 Pro

## 1. System Overview

This document outlines the architecture and design principles of the Farsi History Knowledge Graph project. The system is a comprehensive data pipeline designed to ingest unstructured Farsi text from a series of books, process it using a Large Language Model (LLM), and build a rich, queryable knowledge graph in a Neo4j database. The primary goal is to make the deep, interconnected knowledge within the books accessible through a natural language interface.

The system is orchestrated by a central `main.py` script, which provides a user-friendly, menu-driven interface to control all phases of the pipeline.

---

## 2. Core Components & Architecture

### 2.1. Data Ingestion (`convert_pdfs.py`)
- **Source:** A series of five PDF volumes.
- **Technology:** Python with the `PyMuPDF` library.
- **Process:** The script programmatically opens each PDF, iterates through every page to extract text, and concatenates the results into a single, clean `data/book.txt` file encoded in UTF-8.
- **Design Principle (Learned):** Initial attempts using the `pdftotext` command-line utility produced fundamentally corrupted text files. The key learning was that for robust data ingestion, a programmatic, library-based approach (`PyMuPDF`) is vastly superior to relying on external shell utilities, as it provides better error handling and control over the extraction process.

### 2.2. Schema Definition (`src/graph_schema.py`)
- **Purpose:** To serve as the central "brain" or "blueprint" for the AI. It defines the universe of all possible nodes, relationships, and properties the system can understand.
- **Methodology:** A hybrid human-AI approach was used. An initial schema was manually defined, then significantly enriched by using a `discover_schema.py` script to prompt the Gemini API for suggestions. This resulted in a highly detailed schema tailored to the book's specific domain (politics, legal cases, family ties, etc.).
- **Key Features:**
    - **Hierarchical Nodes:** Uses a multi-labeling strategy (e.g., a `LegalCase` is also an `Event` and a `PoliticalEvent`).
    - **Rich Relationships:** Defines a wide array of specific relationships, moving beyond simple facts to capture nuanced actions.

### 2.3. Extraction Pipeline (`main.py`)
- **Technology:** Python, Google Gemini 1.5 Pro API.
- **Process:**
    1.  The book text is divided into overlapping chunks of ~10,000 characters.
    2.  For each chunk, a detailed system prompt is generated. This prompt includes the entire graph schema and instructions for the desired output format.
    3.  The AI is instructed to extract a list of relationships, where each relationship is a JSON object containing `head`, `tail`, `relation`, and a `properties` object for attributes.
    4.  The results are appended to `data/extracted_graph.json`.
- **Key Features:**
    - **Interactive Control:** The user can process chunks in batches, retry failed chunks, or process the entire remaining book.
    - **Resumability & Fault Tolerance:** A `data/progress_stats.json` file tracks successfully processed chunks, failed chunks, and token usage, allowing the process to be stopped and restarted safely.
    - **Cost Management:** The script uses `model.count_tokens()` to calculate input tokens before each API call and retrieves output tokens from the response metadata, providing a clear view of API costs.

### 2.4. Database Population (`src/populate.py`)
- **Technology:** Python, Neo4j, `ijson` library.
- **Process:**
    1.  The script connects to the Neo4j database and ensures uniqueness constraints are created for all node labels to optimize performance and prevent duplicates.
    2.  It streams the `data/extracted_graph.json` file, reading one relationship object at a time to keep memory usage minimal.
    3.  For each object, it uses a single, powerful Cypher query with `UNWIND` and `MERGE` to create the head node, tail node, and the relationship between them with its properties. `MERGE` ensures that no duplicate nodes are ever created.
    4.  It applies hierarchical labels based on rulebooks defined within the script (e.g., adding the `Event` label to all `LegalCase` nodes).
- **Design Principle (Learned):** The use of `ijson` for streaming and `MERGE` for idempotent writes makes the population process highly scalable and safe to re-run at any time.

### 2.5. Natural Language Query Interface (`qa_interface.py`)
- **Technology:** Python, Google Gemini 1.5 Pro API, Neo4j.
- **Process:** This script implements a two-stage AI pipeline for answering user questions.
    1.  **Text-to-Cypher:** The user's question (in any language) is sent to the Gemini API along with the graph schema. The prompt contains highly specific instructions, refined through iterative testing, on how to generate a syntactically correct and efficient Cypher query.
    2.  **Database Execution:** The generated Cypher query is executed against the Neo4j database.
    3.  **Data-to-Text:** The raw Farsi data returned from the database is sent back to the Gemini API in a second call. This prompt asks the AI to synthesize the data into a concise, natural language answer, formulated in the user's original language.
- **Design Principle (Learned):** The most critical aspect of this component is the prompt engineering for the Text-to-Cypher step. The final prompt explicitly instructs the AI to use the database's **Full-Text Index** (`CALL db.index.fulltext.queryNodes(...)`) with wildcards for searching, as this was found to be the only reliable method for handling the ambiguities of natural language names (e.g., "Khomeini" vs. "Ruhollah Khomeini").

---

## 3. Future Development Roadmap (For Next Chat)

The next phase of development will focus on implementing the advanced features defined in the latest version of the `graph_schema.py` and `main.py` files.

1.  **Implement Relationship Properties in `populate.py`:**
    - The `populate.py` script's Cypher query needs to be upgraded. It currently creates relationships but does not set their properties (e.g., `{visibility: "secret"}`). The `apoc.merge.relationship` procedure must be modified to accept and set the `properties` object from the JSON file.
2.  **Implement Hierarchical Labeling in `populate.py`:**
    - The script needs to be updated with the `EVENT_HIERARCHY` and `CONCEPT_HIERARCHY` rulebooks.
    - The Cypher query must be modified to include the `FOREACH` loop that adds these secondary, thematic labels to the nodes after they are created.
3.  **Full Data Extraction:**
    - Once the `populate.py` script is finalized, the next step is to run the extraction process for all remaining chunks of the book to create a complete `extracted_graph.json`.
4.  **Full Data Population:**
    - Run the finalized `populate.py` script to build the complete, richly detailed knowledge graph in Neo4j.
5.  **Advanced Querying and Analysis:**
    - Begin a new phase of deep analysis by writing and testing complex Cypher queries and using the QA interface to explore the fully populated graph.