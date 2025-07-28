# Implementation Details: AI-Driven Schema Standardization

**Date:** July 29, 2024
**Author:** Gemini 2.5 Pro, assisting Teymoor Kh

## 1. Objective

The primary objective of this process was to address a critical data quality issue in the project: the lack of a standardized schema for relationship types. The initial full-text extraction produced a large set of inconsistent, Farsi-language relationship types. Our goal was to convert this "dirty" schema into a clean, canonical, and maintainable English-language schema to be used as the official standard for the entire project.

## 2. The Initial Challenge

The starting point was the `data/extracted_graph.json.250728.full` file. This file, while comprehensive, contained several issues that would hinder future development:

*   **Inconsistency:** The same conceptual relationship was often represented by multiple different Farsi phrases (e.g., "تاسیس کرد", "بنیان نهاد").
*   **Language Barrier:** The schema elements (relationship types) were in Farsi, while best practice dictates keeping the structural elements of a database in English for easier development, querying, and tool compatibility.
*   **Lack of Convention:** There was no enforced naming convention, leading to a mix of different phrasings and styles.
*   **Scale:** With over 1,000 unique relationship types discovered, a manual review and standardization process would be prohibitively time-consuming and prone to error.

## 3. The Strategy: AI-Assisted Refinement

To overcome the challenge of scale, we opted for a hybrid human-AI strategy. Instead of having a human manually process all 1,000+ terms, we decided to use the Gemini LLM as an intelligent "data architect" assistant.

The strategy was as follows:
1.  Create a new script, `src/refine_schema_from_json.py`.
2.  This script would first programmatically scan the large JSON file to extract a unique list of all Farsi relationship types.
3.  It would then send *only this unique list* to the Gemini API.
4.  A carefully engineered prompt would instruct the AI to translate the conceptual meaning, merge synonymous terms, and standardize the naming convention to `UPPER_SNAKE_CASE`.
5.  The AI's response, a JSON map from the old Farsi types to the new English types, would be saved for final human review.

## 4. The Implementation Journey: Errors and Solutions

The execution of this strategy involved a real-world debugging process that significantly improved the robustness of our code.

### 4.1. First Execution: The `NoneType` Data Quality Error

*   **Action:** We ran the initial version of `refine_schema_from_json.py`.
*   **Result:** The script failed with the error: `'<' not supported between instances of 'NoneType' and 'str'`.
*   **Diagnosis:** The script had successfully found 1037 "unique" items. The error occurred in the `sorted()` function, indicating that at least one of the items was not a string, but was the Python `None` value. This was caused by entries in the source JSON like `{"relation": null}`.
*   **Resolution:** We made the script more robust by modifying the scanning logic. The new code explicitly checks if the value associated with the `"relation"` key is a valid, non-empty string before adding it to the set of unique relations.

### 4.2. Second Execution: The JSON Decode Error and the "Self-Correction Loop"

*   **Action:** We ran the corrected script.
*   **Result:** The script successfully scanned the file, found 1036 valid relationship types, and received a response from the Gemini API. However, it then failed with a `json.JSONDecodeError: Unterminated string`.
*   **Diagnosis:** The text returned by the AI, while intended to be JSON, contained a syntax error that made it invalid. This is a common issue when generating large, structured text outputs with LLMs.
*   **Resolution:** Instead of simply retrying, we implemented a more intelligent **"self-correction loop."** The script was modified to:
    1.  `try` to parse the AI's response.
    2.  If it fails, `catch` the `JSONDecodeError`.
    3.  Send a **new prompt** back to the AI. This prompt includes the AI's own faulty text along with the specific error message, and instructs the AI to fix its mistake.
    4.  This loop was set to retry up to 3 times.

### 4.3. Third Execution: Success Through Self-Correction

*   **Action:** We ran the final, robust version of the script.
*   **Result:** The process executed perfectly.
    *   **Attempt 1:** The AI returned faulty JSON, which was caught by our error handler.
    *   **Attempt 2:** The script sent the error back to the AI, which then provided a corrected, valid JSON response.
    *   The script successfully parsed the corrected response.

## 5. Outcome

The process concluded successfully with the creation of the `data/suggested_schema_map.json` file. This file contains a comprehensive JSON object mapping the 1036 original Farsi relationship types to a clean, standardized, and consolidated set of English relationship types.

This file now serves as the high-quality draft for our official project schema, ready for the final step of human review and curation.