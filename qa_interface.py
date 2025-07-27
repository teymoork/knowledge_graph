import os
import sys
import google.generativeai as genai
from neo4j import GraphDatabase

# --- Path Correction ---
# Add the 'src' directory to Python's path to allow imports from it
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
# --- End Path Correction ---

import config
from graph_schema import NodeLabel, RelationshipLabel

def get_schema_representation() -> str:
    """
    Generates a string representation of the graph schema for the LLM prompt.
    """
    node_labels = [f"`{label.value}`" for label in NodeLabel]
    rel_labels = [f"`{label.value}`" for label in RelationshipLabel]
    
    return f"""
# Node Labels in the Database:
{', '.join(node_labels)}

# Relationship Labels in the Database:
{', '.join(rel_labels)}
"""

def generate_cypher_prompt(schema: str, question: str) -> str:
    """
    Creates the full prompt to send to the LLM for Cypher generation.
    """
    return f"""
You are an expert Neo4j developer who is fluent in both English and Farsi. Your task is to convert a user's question, which will be in Farsi, into a single, valid Cypher query.

You must use the following database schema. The node labels, relationship labels, and all data in the `name` property of the nodes are in Farsi.

# Database Schema:
{schema}

# Instructions:
1.  Analyze the user's question in Farsi.
2.  Construct a Cypher query that accurately answers the question using ONLY the provided schema.
3.  When matching nodes, use the `name` property (e.g., `MATCH (p:شخص {{name: 'روح‌الله خمینی'}})`).
4.  Your final output must be ONLY the Cypher query. Do not include any explanations, introductory text, or markdown formatting like ```cypher.

# User's Question:
{question}

# Cypher Query:
"""

def main():
    """
    Main function to run the conversational QA interface.
    """
    print("--- Farsi Knowledge Graph QA Interface ---")
    print("Type your question in Farsi, or type 'quit' to exit.")

    # 1. Configure APIs and Database
    try:
        genai.configure(api_key=config.GOOGLE_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-pro-latest')
        
        db_driver = GraphDatabase.driver(
            config.NEO4J_URI, 
            auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
        )
        db_driver.verify_connectivity()
        print("Successfully connected to Gemini API and Neo4j Database.")
    except Exception as e:
        print(f"ERROR: Failed to initialize connections. Details: {e}")
        return

    # 2. Get schema representation
    schema_str = get_schema_representation()

    # 3. Start conversational loop
    while True:
        user_question = input("\nYour question: ")
        if user_question.lower() in ['quit', 'exit']:
            print("Exiting.")
            break

        # 4. Generate Cypher from the user's question
        try:
            print("Translating your question into a database query...")
            prompt = generate_cypher_prompt(schema_str, user_question)
            response = model.generate_content(prompt)
            cypher_query = response.text.strip()
            
            # Clean up potential markdown formatting from the LLM
            if cypher_query.startswith("```cypher"):
                cypher_query = cypher_query.replace("```cypher", "").strip()
            if cypher_query.endswith("```"):
                cypher_query = cypher_query.replace("```", "").strip()

            print(f"Generated Cypher: {cypher_query}")

        except Exception as e:
            print(f"ERROR: Could not generate Cypher query. Details: {e}")
            continue

        # 5. Execute the Cypher query
        try:
            print("Executing query...")
            with db_driver.session() as session:
                result = session.run(cypher_query)
                records = list(result) # Consume the result to get all records

                if not records:
                    print("\n--- Query returned no results. ---")
                else:
                    print("\n--- Query Results ---")
                    for i, record in enumerate(records):
                        print(f"Result {i+1}:")
                        for key, value in record.items():
                            # Handle nodes and relationships to print them nicely
                            if hasattr(value, 'labels'): # It's a node
                                print(f"  - {key}: (Labels: {list(value.labels)}, Name: {value.get('name')})")
                            elif hasattr(value, 'type'): # It's a relationship
                                print(f"  - {key}: (Type: {value.type})")
                            else: # It's a property value
                                print(f"  - {key}: {value}")
                    print("---------------------")

        except Exception as e:
            print(f"ERROR: Failed to execute Cypher query. Details: {e}")
            continue
            
    db_driver.close()

if __name__ == "__main__":
    main()