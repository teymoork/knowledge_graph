# Farsi History Knowledge Graph

## 1. Project Overview

This project is a sophisticated data pipeline and knowledge discovery engine designed to transform unstructured Farsi historical texts into a structured, queryable knowledge graph. By leveraging Large Language Models (LLMs) and a Neo4j graph database, the system extracts complex relationships between people, organizations, events, and concepts, making deep historical knowledge accessible through a natural language interface.

The project has successfully moved beyond initial data extraction and is now entering a phase of AI-driven knowledge discovery, where the system itself will help to uncover and define new, high-level concepts hidden within the data.

## 2. Current Status

**Phase 1: Core Pipeline - ✅ Complete**
-   **Data Ingestion:** Successfully ingests and cleans text from source PDFs.
-   **AI-Powered Extraction:** The core pipeline can extract entities and relationships from text chunks based on a predefined schema.
-   **Database Population:** The system can reliably populate a Neo4j database, correctly creating nodes with hierarchical labels and relationships with specific properties.
-   **QA Interface:** A functional natural language query interface allows users to ask questions and receive synthesized answers from the graph.

**Phase 2: AI-Driven Schema Evolution - 🚧 In Progress**
-   The project's current focus is on developing a "Schema Discovery Loop." This advanced feature will use the LLM to analyze the existing graph, identify meaningful patterns, and propose new, high-level relationships to enrich the schema. This will enable the discovery of knowledge that is not explicitly stated in any single piece of text.

## 3. Core Features

*   **Hierarchical Data Model:** Nodes are classified with multiple labels (e.g., a `LegalCase` is also a `PoliticalEvent` and an `Event`), allowing for powerful, multi-level queries.
*   **Rich Relationships:** The graph captures nuanced actions and attributes by storing detailed properties on the relationships themselves.
*   **Resilient Pipeline:** The extraction process is designed to be resumable and fault-tolerant, tracking progress and API costs.
*   **Natural Language Querying:** A two-stage AI process translates user questions (in any language) into database queries and then synthesizes the results into natural language answers.
*   **AI-Powered Schema Discovery (In Development):** A feedback loop where the AI acts as a "Knowledge Graph Analyst" to suggest new concepts and relationships, enabling continuous learning and graph enrichment.

## 4. Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd knowledge_graph
    ```
2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Configure Environment:**
    -   Create a `.env` file in the project root.
    -   Add your Neo4j database credentials and Google API key to this file:
        ```
        NEO4J_URI="bolt://localhost:7687"
        NEO4J_USER="neo4j"
        NEO4J_PASSWORD="your_neo4j_password"
        GOOGLE_API_KEY="your_google_api_key"
        ```
4.  **Ensure Neo4j is running.** For users with a Docker-based setup, ensure your Neo4j container is active.

## 5. Project Workflow and Usage

This section outlines the step-by-step process for running the entire pipeline, from initial setup to a fully populated and queryable knowledge graph.

### **Phase A: Initial Setup & Schema Generation (One-Time Process)**

This phase is performed once to create the initial, standardized schema.

1.  **Generate Raw Farsi Extractions:**
    -   Use the `src/main.py` script to perform a full extraction on your source text (`data/book.txt`). This will produce a large JSON file with unstandardized Farsi relationship types (e.g., `data/extracted_graph.json.250728.full`).

2.  **Generate the Curated Schema Map:**
    -   Run the advanced curation script:
        ```bash
        python src/util/bulk_curate_v2.py
        ```
    -   This performs a multi-stage, AI-powered process to create a draft of the schema map.
    -   **Crucial Manual Step:** Open the output file, `data/curated_schema_map.json`, and manually review it. Search for any remaining placeholders (`NEEDS_VERB_FOR_...`) and refine any other AI suggestions to ensure the schema is perfect.

3.  **Update the Official Schema File:**
    -   Run the population utility to inject your curated map into the project's official schema file:
        ```bash
        python src/util/populate_schema_file.py
        ```
    -   This updates `src/graph_schema.py`, which is now the definitive source of truth for the project.

### **Phase B: Standardized Data Generation & Population**

This is the standard operational phase.

4.  **Translate Existing Data to the New Schema:**
    -   Run the translation utility to upgrade your raw Farsi extraction file to the new English schema:
        ```bash
        python src/util/translate_existing_graph.py
        ```
    -   This reads your raw data and your curated map, and writes a new, clean file: `data/extracted_graph_english_schema.json`.

5.  **Populate the Neo4j Database:**
    -   Run the population script. **Note:** This script is hardcoded to read from `data/extracted_graph.json`. You should rename your new, clean file (`extracted_graph_english_schema.json`) to `extracted_graph.json` before running this step.
        ```bash
        # First, rename the file:
        mv data/extracted_graph_english_schema.json data/extracted_graph.json

        # Then, run the populator:
        python src/populate.py
        ```

### **Phase C: Interaction and Future Work**

6.  **Query the Graph:**
    -   Launch the main project interface to access the QA system:
        ```bash
        python src/main.py
        ```
    -   Select option "3. Ask Questions (QA Interface)".

7.  **Extract New Data (Optional):**
    -   If you add new source texts, you can run the extraction pipeline again via the `src/main.py` menu. It is now configured to automatically use the clean, official English schema for all new extractions.

## 6. Project Conclusion and Key Learnings

This project successfully achieved its technical goal: to build an end-to-end pipeline that transforms unstructured Farsi text into a queryable knowledge graph. The most valuable outcome, however, was the deep insight gained into the strengths and limitations of this approach for analyzing complex historical narratives.

### Strengths of the Knowledge Graph Approach

*   **Fact Structuring:** The **Knowledge Graph (KG)** is exceptionally good at extracting and structuring explicit, factual statements (e.g., Person A was a `MEMBER_OF` Organization B; Event C `OCCURRED_ON` Date D).
*   **Network Visualization:** It provides a powerful way to visualize and explore the network of connections between entities, revealing non-obvious clusters and relationships.
*   **Precise, Structured Querying:** For questions with a clear structure ("List all members of X"), the graph provides fast, accurate, and reliable answers.

### Limitations for Deep Semantic Analysis

Through rigorous testing of the final QA interface, we discovered the fundamental limitations of a structured graph when dealing with the ambiguity and richness of human language and narrative.

*   **Brittleness of the Schema:** The graph is literal. A query for the relationship `OPPOSED` will fail if the data only contains the relationship `CRITICIZED`, even though they are semantically similar. The Text-to-Cypher AI can be taught to search for multiple types, but it is essentially guessing from a fixed list and can easily miss the correct one.
*   **Loss of Narrative Context:** The process of breaking down a complex narrative into discrete `(head)-[relation]->(tail)` triplets inherently loses the author's tone, intent, and the subtle, implicit meaning that connects sentences. A question like "What was the *nature* of the relationship between Person A and Person B?" is very difficult for a graph to answer, as it cannot easily represent concepts like sarcasm, evolving opinions, or trust.
*   **The "Guessing Game":** The Text-to-Cypher AI must constantly "guess" the exact name of a node (e.g., "Bani Sadr" vs. "Abolhassan Banisadr") and the exact relationship type that was extracted. As we saw, even a near-perfect guess can result in a failed query.

### Final Recommendation

A Knowledge Graph is an invaluable tool for creating a structured, queryable **database of facts** from a text. It excels at answering "who," "what," "where," and "when."

However, for the deepest semantic analysis—understanding the "why" and "how" that is embedded in narrative context and authorial voice—the KG should be seen as a **complementary tool, not a replacement for direct language model analysis.** A hybrid approach, where the KG is used to find key entities and events, and a separate LLM process is used to analyze the raw text surrounding those entities, would likely yield the most profound insights. This project serves as a powerful and successful demonstration of this critical distinction.