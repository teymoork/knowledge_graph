import os
from dotenv import load_dotenv
import google.generativeai as genai
from neo4j import GraphDatabase
import json

# --- Import the schema lists ---
from src.graph_schema import BASE_NODE_LABELS, RELATIONSHIP_TYPES

# --- Configuration ---
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# --- Prompt Generation ---
def generate_cypher_prompt():
    """
    Generates the final, definitive system prompt for the Text-to-Cypher AI.
    """
    node_labels_str = "`, `".join(BASE_NODE_LABELS)
    relationship_types_str = "`, `".join(RELATIONSHIP_TYPES)

    return f"""
    You are an expert Neo4j Cypher query generator. Your task is to convert a user's question in natural language into a Cypher query.

    **DATABASE SCHEMA:**
    - **Node Labels:** `{node_labels_str}`
    - **Relationship Types:** `{relationship_types_str}`
    - **Node Properties:** All nodes have a `name` property.
    - **Relationship Properties:** Relationships can have properties like `reason`, `year`, `note`, `type`, etc.

    **CRITICAL INSTRUCTIONS:**
    1.  You MUST use the provided Node Labels and Relationship Types.
    2.  For searching node names, ALWAYS use the full-text index with a fuzzy match: `CALL db.index.fulltext.queryNodes("node_names", "some name~") YIELD node, score`
    3.  Return ONLY the Cypher query.

    **QUERYING STRATEGIES & EXAMPLES:**
    - **Complex Actions:** For "opposition" or "support," search for a LIST of related relationship types.
      - **Question:** "Who opposed Bani Sadr?"
      - **Cypher:** `CALL db.index.fulltext.queryNodes("node_names", "بنی صدر~") YIELD node AS target MATCH (person)-[r:OPPOSED|CRITICIZED|DENOUNCED]->(target) RETURN person.name`
    
    - **Relationship Properties:** For "why," "when," or "how," return the ENTIRE relationship object `r`. This is the most robust method.
      - **Question:** "Why was Amir-Entezam accused?"
      - **Cypher:** `CALL db.index.fulltext.queryNodes("node_names", "امیرانتظام~") YIELD node AS target MATCH (accuser)-[r:ACCUSED|ACCUSED_IN]-(target) RETURN r`
    """

# --- Main QA Logic ---
def run_qa_interface():
    """Main loop for the question-answering interface."""
    print("\n--- Natural Language QA Interface (v4 - Definitive) ---")
    print("Ask a question about the Farsi History Knowledge Graph.")

    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        driver.verify_connectivity()
    except Exception as e:
        print(f"FATAL: Could not connect to Neo4j database. Error: {e}")
        return

    cypher_model = genai.GenerativeModel('gemini-1.5-pro-latest')
    synthesis_model = genai.GenerativeModel('gemini-1.5-pro-latest')
    cypher_prompt_template = generate_cypher_prompt()

    while True:
        # --- MODIFIED: Improved user prompt ---
        user_question = input("\nYour Question (type 'exit' to return to main menu): ")
        if user_question.lower() in ['exit', 'quit']:
            break
        if not user_question:
            continue

        print("1. Generating Cypher query...")
        try:
            full_cypher_prompt = cypher_prompt_template + f"\n**User Question:** \"{user_question}\""
            cypher_response = cypher_model.generate_content(full_cypher_prompt)
            generated_cypher = cypher_response.text.strip().replace("```cypher", "").replace("```", "")

            if "ERROR" in generated_cypher or not generated_cypher:
                print("   - AI could not generate a valid query for this question.")
                continue
            
            print(f"   - Generated Query:\n{generated_cypher}")
        except Exception as e:
            print(f"   - An error occurred during Cypher generation: {e}")
            continue

        print("2. Executing query against Neo4j...")
        try:
            with driver.session(database="neo4j") as session:
                result = session.run(generated_cypher)
                # We now handle relationship objects correctly
                records = [record.data() for record in result]
            
            if not records:
                print("   - Your query returned no results from the database.")
                continue
            
            print(f"   - Found {len(records)} records.")
        except Exception as e:
            print(f"   - An error occurred during database execution: {e}")
            continue

        print("3. Synthesizing a natural language answer...")
        try:
            synthesis_prompt = f"""
            You are an AI assistant. Your task is to answer a user's question based on the data provided.
            Answer concisely in the same language as the original question.

            Original Question: "{user_question}"

            Data from Database (in JSON format):
            {json.dumps(records, ensure_ascii=False, indent=2)}

            Answer:
            """
            synthesis_response = synthesis_model.generate_content(synthesis_prompt)
            final_answer = synthesis_response.text
            
            print("\n--- Answer ---")
            print(final_answer)
            print("--------------")

        except Exception as e:
            print(f"   - An error occurred during answer synthesis: {e}")
            continue
    
    driver.close()
    print("\nReturning to main menu...")

if __name__ == "__main__":
    run_qa_interface()