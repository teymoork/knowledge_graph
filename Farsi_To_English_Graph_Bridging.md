# Technical Whitepaper: Bridging Farsi Text to an English-Schema Knowledge Graph

**Project:** Farsi History Knowledge Graph
**Date:** July 30, 2024
**Author:** Gemini 2.5 Pro, assisting Teymoor Kh

## 1. The Core Challenge: Semantic and Structural Mismatches

The primary goal of this project is to convert unstructured, historical Farsi text into a highly structured knowledge graph with a standardized English schema. This presents a significant challenge that goes far beyond simple translation. The core problems can be summarized as:

*   **Semantic Ambiguity:** A single Farsi phrase can have multiple nuances. The AI's initial interpretation might be too broad or contextually incorrect.
*   **Synonym Proliferation:** The same conceptual action can be described with many different Farsi verbs and phrases (e.g., "founded," "established," "created"). A naive extraction would result in a messy, redundant graph schema.
*   **Grammatical Variation:** The extraction process must account for active vs. passive voice, pluralization, and the inclusion of prepositions (e.g., "arrested," "was arrested," "was arrested in").
*   **Problem of Scale:** An initial extraction on the full text yielded **1036** unique Farsi relationship types, making any form of manual standardization prohibitively time-consuming and prone to error.

## 2. The Strategic Rationale for an English-Language Schema

Before detailing the implementation, it is crucial to understand the strategic decision to translate the Farsi relationship types into a standardized English schema. This was not merely a cosmetic change; it was a foundational architectural decision made to enhance the project's power, reliability, and maintainability. The rationale is threefold: Standardization, AI Comprehension, and Developer Ergonomics.

### 2.1. Standardization: From Ambiguity to Canonical Concepts

This is the most critical reason. The initial, raw extraction from the Farsi text was conceptually "dirty." It contained over 1000 unique relationship strings, many of which were synonyms or slight grammatical variations of the same core idea.

*   **The Problem (Before):** The graph contained a multitude of relationship types for the concept of "founding," such as `"تاسیس کرد"`, `"بنیان نهاد"`, and `"ایجاد نمود"`. This redundancy makes querying the graph extremely difficult and brittle. To find all organizations founded by a person, a developer would need to know every possible synonym and write a complex query:
    ```cypher
    MATCH (p)-[r]->(o)
    WHERE type(r) IN ["تاسیس کرد", "بنیان نهاد", "ایجاد نمود", ...]
    RETURN p, o
    ```
    This approach is not scalable and is guaranteed to miss variations, leading to incomplete query results.

*   **The Solution (After):** The translation process was used as a forcing function to achieve **conceptual consolidation**. By mapping all these Farsi synonyms to a single, canonical English relationship type—`FOUNDED`—we transformed the schema. The query becomes simple, robust, and guaranteed to be complete:
    ```cypher
    MATCH (p)-[:FOUNDED]->(o) RETURN p, o
    ```
    The result is a clean, curated vocabulary of **755 unique, unambiguous actions**, reduced from over 1000 ambiguous ones. This standardization makes the entire graph more powerful and its data more reliable.

### 2.2. AI Comprehension: Enabling Advanced Features

The project's most advanced features, particularly the Natural Language QA Interface (`qa_interface.py`), rely on sending the graph's schema to the Gemini API. The AI uses this schema as a "toolbox" to understand what kind of Cypher queries it is allowed to generate.

*   **The Problem:** Providing the AI with a schema of 1000+ Farsi variations, including complex grammar and right-to-left text, significantly increases its cognitive load. This ambiguity raises the probability of the AI misinterpreting a user's question or generating a syntactically incorrect Cypher query, leading to failed responses and an unreliable user experience.

*   **The Solution:** By providing the AI with a clean, curated list of 755 `UPPER_SNAKE_CASE` English verbs, we give it a clear, unambiguous set of tools. This standardized, machine-friendly format makes it much easier for the AI to map a user's natural language question (whether asked in Farsi, English, or another language) to the correct relationship type in the database. This dramatically increases the accuracy and reliability of the entire QA system.

### 2.3. Developer Ergonomics: A Maintainable and Scalable System

A knowledge graph is a software system that must be maintained and extended by developers. Adhering to established software engineering best practices is crucial for the project's long-term health.

*   **The Problem:** Using a non-English, right-to-left language for core schema elements introduces significant friction into the development workflow. It can cause issues with text encoding, terminal rendering, and makes the code harder to read, debug, and contribute to, especially for a diverse team.

*   **The Solution:** We adopted the industry-standard convention of separating the **data** from the **schema**.
    *   **Schema (The Structure):** Node labels, relationship types, and property keys are defined in English (`Person`, `FOUNDED`, `reason`). This is the language of the code and the database structure.
    *   **Data (The Content):** The actual values within the nodes and properties remain in the original Farsi (`name: 'سیدمحمد حسینی بهشتی'`), preserving the integrity of the source material.

This separation makes the developer's job simpler, the code cleaner, and the project as a whole more robust and maintainable.

## 3. The Implementation: A Step-by-Step Walkthrough

The final, successful methodology was an evolution, born from troubleshooting earlier, simpler approaches that failed under the complexity of the task. The definitive process is a three-stage automated curation pipeline executed by the `src/util/bulk_curate_v2.py` script.

### Step 3.1: Initial Data Extraction

The process begins with a comprehensive but "dirty" data file, `data/extracted_graph.json.250728.full`. This file was generated by running an early version of the extraction pipeline over the entire book. While the relationships extracted were conceptually valuable, the labels themselves were unstandardized Farsi strings. This file serves as the raw input for our schema refinement.

### Step 3.2: Initial AI-Powered Mapping

The first attempt at standardization involved sending the 1036 unique Farsi terms to the Gemini API to request a direct Farsi-to-English mapping. This produced the `data/suggested_schema_map.json` file. However, a detailed analysis revealed that the quality of the AI's suggestions was low; it frequently used generic nouns (`EVENT`, `LEGAL`) instead of specific verbs.

### Step 3.3: The Definitive Three-Stage Curation Process (`bulk_curate_v2.py`)

This script represents our refined, robust solution. It takes the low-quality `suggested_schema_map.json` as input and produces a high-quality `curated_schema_map.json` as output.

#### Stage 1: Local Rule-Based Curation

The script first performs a rapid, local pass on all mappings. It applies a set of deterministic rules we developed based on our manual analysis to perform easy fixes and flag all terms that required a proper verb.

#### Stage 2: AI-Powered Verb Generation (in Batches)

This is the core of the advanced automation. The script takes the list of flagged "hard problems" from Stage 1 and, to ensure reliability, breaks it into smaller **batches**. It then iterates through these batches, sending each to the Gemini API with a highly focused prompt to generate a specific English verb for each Farsi term.

#### Stage 3: Final Assembly & Human Review

The script merges the results from the two previous stages into a final `curated_schema_map.json` file. This file is the product of the automated pipeline and is then passed to the human expert for a final, rapid review to catch any remaining subtle errors.

## 4. The Outcome: A Standardized and Curated Schema Map

The final artifact of this entire process is the `data/curated_schema_map.json` file. This file is the bridge that allows us to reliably and consistently convert the conceptual richness of the Farsi text into the rigid, logical structure of our English-schema knowledge graph.