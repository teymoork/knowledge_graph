import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

# --- Configuration ---
load_dotenv()
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

def get_graph_schema_summary(tx):
    """
    Queries the database to get a list of all node labels and relationship types.
    """
    labels_query = "CALL db.labels() YIELD label RETURN collect(label) as labels"
    rels_query = "CALL db.relationshipTypes() YIELD relationshipType RETURN collect(relationshipType) as rels"
    
    labels = tx.run(labels_query).single()['labels']
    relationships = tx.run(rels_query).single()['rels']
    
    return labels, relationships

def propose_updates():
    """
    Main function to connect to the database and generate a summary of its schema.
    """
    print("Connecting to Neo4j to analyze graph schema...")
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        driver.verify_connectivity()
        print("Connection successful.")
    except Exception as e:
        print(f"Error connecting to Neo4j: {e}")
        return

    with driver.session(database="neo4j") as session:
        node_labels, relationship_types = session.execute_read(get_graph_schema_summary)
        
        print("\n--- Current Graph Schema Summary ---")
        print(f"\nNode Labels ({len(node_labels)}):")
        for label in sorted(node_labels):
            print(f"- {label}")
            
        print(f"\nRelationship Types ({len(relationship_types)}):")
        # We sort them to ensure consistent output for the LLM
        for rel_type in sorted(relationship_types):
            print(f"- {rel_type}")
        
        # --- TODO: Next steps ---
        # 1. Generate a text summary for the LLM.
        # 2. Create and send the "Schema Analyst" prompt.
        # 3. Process the LLM's response.
        
    driver.close()
    print("\nAnalysis complete. Database connection closed.")

if __name__ == "__main__":
    propose_updates()