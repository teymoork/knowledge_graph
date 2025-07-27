# Farsi History Knowledge Graph

## 1. Project Objective

The goal of this project is to process a history book written in Farsi using a Large Language Model (LLM) to build a comprehensive knowledge graph. This graph captures historical entities (people, places, events) and the complex relationships between them, making the book's content queryable through a natural language interface.

## 2. Core Technologies

*   **Programming Language:** Python 3.10+
*   **Dependency Management:** Poetry
*   **AI Model:** Google Gemini 1.5 Pro (via Google AI Studio / Vertex AI)
*   **Graph Database:** Neo4j (Community Edition), run via Docker.
*   **Core Python Libraries:**
    *   `google-generativeai`: To interact with the Gemini API.
    *   `neo4j`: The official Python driver for Neo4j.
    *   `PyMuPDF`: For robust, high-quality PDF-to-text conversion.
    *   `ijson`: For memory-efficient streaming of large JSON files.
    *   `python-dotenv`: To manage API keys and configuration securely.
    *   `tqdm`: For displaying progress bars during long processing jobs.

## 3. Project Workflow

This project is managed by a central `main.py` script which provides an interactive menu to orchestrate the entire pipeline:

1.  **Data Preparation:** A `convert_pdfs.py` script uses `PyMuPDF` to convert the source PDF books into a single, clean `data/book.txt` file.
2.  **Schema Discovery:** A `discover_schema.py` script samples the book and uses the Gemini API to suggest new, meaningful relationship types, enabling a rich, data-driven schema.
3.  **Extraction:** The main script manages an interactive process to read the book in chunks and send them to the Gemini API. The AI extracts triplets (head, relation, tail) based on our detailed schema and saves them to `data/extracted_graph.json`. The process is resumable and tracks progress, including failed chunks.
4.  **Population:** A memory-efficient `populate.py` script streams the extracted JSON data and populates the Neo4j database. It uses idempotent `MERGE` commands to prevent data duplication.
5.  **Querying:** A `qa_interface.py` script provides a conversational interface. It takes questions in plain Farsi, uses the Gemini API to translate them into Cypher queries, executes them against the database, and returns the results in a human-readable format.

## 4. How to Run

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/teymoork/knowledge_graph.git
    cd knowledge_graph
    ```

2.  **Set up environment variables:**
    Create a `.env` file in the project root and add your credentials.
    ```env
    # Neo4j Database Credentials
    NEO4J_PASSWORD=your-secure-password-here

    # Google Gemini API Key
    GOOGLE_API_KEY="your-google-api-key-here"
    ```

3.  **Start the Neo4j Database:**
    Make sure you have Docker installed and running.
    ```bash
    docker compose up -d
    ```

4.  **Install dependencies:**
    Make sure you have Poetry installed.
    ```bash
    poetry install
    ```

5.  **Run the main interface:**
    ```bash
    poetry run python main.py
    ```
    This will launch the main menu where you can control the entire pipeline.