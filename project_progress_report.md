# Final Project Progress Report

**Project:** Farsi History Knowledge Graph
**Date:** August 1, 2024
**Status:** Core Pipeline Complete; Key Insights Gained

## 1. Executive Summary

This document details the complete development lifecycle of the Farsi History Knowledge Graph project, from initial implementation to final testing and analysis. The project successfully achieved its primary technical objective: to build a fully automated, end-to-end pipeline that ingests unstructured Farsi text, extracts structured data using an LLM, populates a Neo4j graph database, and provides a natural language query interface.

The most significant outcome of the project was not just the creation of the technical artifact, but the profound insights gained into the practical application of knowledge graphs for deep semantic analysis of historical narratives. Through a rigorous process of implementation, debugging, and testing, we were able to clearly identify the powerful capabilities and inherent limitations of this approach. This report concludes that while knowledge graphs are unparalleled for structuring and querying explicit facts, they are best used as a complementary tool alongside direct LLM analysis for understanding the deeper, implicit context of a text.

## 2. The Development Journey: From Theory to a Hardened System

The development process was an iterative cycle of implementation and real-world debugging. This journey was critical in transforming a theoretical design into a robust, functional system.

### 2.1. Schema Standardization: The Core Task

The central and most complex phase of the project was the creation of a standardized, canonical schema for relationship types.

*   **Initial State:** A raw extraction from the source text yielded over 1000 unstandardized, Farsi-language relationship types, rife with synonyms and grammatical variations.
*   **Strategy Evolution:** Our approach evolved significantly:
    1.  An initial attempt to have an AI map all 1000+ terms in a single pass failed due to the task's complexity, resulting in incomplete and low-quality suggestions.
    2.  A second attempt using batch processing solved the reliability issue but introduced a new problem: synonyms in different batches were not being consolidated.
    3.  The final, successful strategy was a **three-stage automated curation pipeline (`bulk_curate_v2.py`)**:
        *   **Stage 1 (Local Rules):** A script first applied deterministic rules to fix simple issues and flag complex cases.
        *   **Stage 2 (AI Verb Generation):** The script then sent the "hard" cases to the Gemini API in small, manageable batches with a highly focused prompt, asking only for specific verb generation.
        *   **Stage 3 (Assembly & Human Review):** The script assembled the results into a final `curated_schema_map.json`, which was then given a final, rapid review by the human expert.
*   **Outcome:** This hybrid process successfully consolidated over 1000 Farsi variations into a clean, canonical schema of 755 English `UPPER_SNAKE_CASE` relationship types.

### 2.2. Data Pipeline Hardening

The process of populating the database with over 11,000 extracted relationships revealed numerous data quality and system integration issues, all of which were systematically solved:

*   **Data Validation:** The `populate.py` script was progressively hardened to handle a wide range of "dirty data" issues from the AI, including missing keys, `null` values, empty strings, and non-primitive property types (nested objects). The final script is highly resilient to malformed input.
*   **Database Errors:** We debugged and resolved several critical Neo4j errors, including `MergeConstraintConflictException` (by adopting a more robust two-step MERGE/SET Cypher query) and missing index errors (by creating the necessary full-text index).
*   **Environment and Pathing:** We resolved multiple Python `ModuleNotFoundError` issues by correcting the import logic to be compatible with the project's `src` layout.

### 2.3. QA Interface Refinement

Testing the `qa_interface.py` was the final and most illuminating phase. It revealed the challenges of translating human intent into precise database queries.

*   **Initial Failure:** Early questions failed because the Text-to-Cypher AI made logical but incorrect "guesses" about the exact names of nodes (e.g., "Bani Sadr" vs. "Abolhassan Banisadr") and the specific relationship types to use.
*   **Prompt Engineering:** We iteratively improved the AI's prompt, "teaching" it more robust querying strategies. The final prompt instructs the AI to:
    1.  Use fuzzy, wildcard searches on node names (`... "Bani Sadr~"`).
    2.  Search for a list of semantically related relationship types (`[:OPPOSED|CRITICIZED|DENOUNCED]`).
    3.  Query for the entire relationship object (`RETURN r`) when asked about properties, making the query more general and robust.
*   **Success:** The final version of the QA interface proved capable of answering complex questions by generating sophisticated, multi-faceted Cypher queries.

## 3. Final Conclusion and Strategic Recommendation

The project was a definitive success. It not only produced a functional knowledge graph pipeline but also served as a powerful research tool into the nature of AI-driven text analysis.

**The key takeaway is the distinction between a database of facts and a tool for semantic understanding.**

*   **The Knowledge Graph as a Factual Database:** The system we built is exceptionally effective at this. It successfully extracts explicit factual claims and structures them in a way that is perfect for precise queries. For answering "who," "what," "where," and "when," it is a powerful and reliable tool.

*   **The Limitation for Deep Analysis:** The process of deconstructing a narrative into atomic `(head)-[relation]->(tail)` triplets, by its very nature, strips away the author's nuanced voice, the implicit connections between statements, and the overall narrative context. The final QA system, while powerful, is ultimately playing a "guessing game" to translate ambiguous human language into the rigid, literal logic of the graph. A near-miss in this guessing game results in a failed query.

**Recommendation:** This knowledge graph should be viewed as a foundational component of a larger analytical toolkit. It provides an incredible "index" to the source text. A future, more advanced system would use this graph to quickly identify key entities, events, and their direct relationships. It would then feed the *original raw text* associated with those graph components back to an LLM with a prompt designed for deep semantic analysis, asking questions like, "Based on these passages, what was the author's opinion of this event?"

This hybrid, two-step approach—using the graph to find *what* to look at, and an LLM to understand *how* to interpret it—represents the most promising path forward for deep, semantic analysis of complex texts.