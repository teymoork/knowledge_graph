import os
import sys
import json
import ijson
from neo4j import GraphDatabase
from dotenv import load_dotenv
from tqdm import tqdm

# --- Sibling Import Fix ---
from graph_schema import BASE_NODE_LABELS, EVENT_HIERARCHY, CONCEPT_HIERARCHY

# --- Configuration ---
load_dotenv()
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
JSON_FILE_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'extracted_graph.json')

# --- Helper Functions ---
def get_all_labels(primary_label: str) -> list[str]:
    """Traverses the hierarchy dictionaries to find all parent labels."""
    if not primary_label or not isinstance(primary_label, str):
        return []
    labels = [primary_label]
    current_label = primary_label
    full_hierarchy = {**EVENT_HIERARCHY, **CONCEPT_HIERARCHY}
    while current_label in full_hierarchy:
        parent_label = full_hierarchy[current_label]
        labels.append(parent_label)
        current_label = parent_label
    return labels

def flatten_properties(props):
    """
    Recursively flattens property values. Converts any dict or list
    found as a value into a JSON string.
    """
    if not isinstance(props, dict):
        return props
    
    flat_props = {}
    for key, value in props.items():
        if isinstance(value, (dict, list)):
            flat_props[key] = json.dumps(value, ensure_ascii=False)
        else:
            flat_props[key] = value
    return flat_props

# --- Neo4j Operations ---
def create_constraints(tx):
    """Ensures uniqueness constraints are created for all base node types."""
    print("Ensuring uniqueness constraints exist...")
    for label in BASE_NODE_LABELS:
        query = f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{label}) REQUIRE n.name IS UNIQUE"
        tx.run(query)
    print("Constraints checked.")

def populate_graph():
    """Streams the JSON file and populates the Neo4j database with the most robust query pattern."""
    print("Connecting to Neo4j database...")
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    driver.verify_connectivity()
    print("Connection successful.")

    with driver.session(database="neo4j") as session:
        session.execute_write(create_constraints)

    cypher_query = """
    UNWIND $batch as row
    MERGE (head {name: row.head_name})
    MERGE (tail {name: row.tail_name})
    WITH head, tail, row
    CALL apoc.create.addLabels(head, row.head_labels) YIELD node AS head_labeled
    CALL apoc.create.addLabels(tail, row.tail_labels) YIELD node AS tail_labeled
    CALL apoc.merge.relationship(head_labeled, row.rel_type, {}, row.rel_props, tail_labeled) YIELD rel
    RETURN count(*) as processed_count
    """

    processed_count = 0
    skipped_count = 0
    batch = []
    batch_size = 500

    print(f"Starting to process {JSON_FILE_PATH}...")
    try:
        with open(JSON_FILE_PATH, 'r', encoding='utf-8') as f:
            relationships = ijson.items(f, 'graph.item')
            
            with driver.session(database="neo4j") as session:
                for rel in tqdm(relationships, desc="Populating Graph"):
                    required_keys = ['head', 'head_label', 'relation', 'tail', 'tail_label', 'properties']
                    if not all(k in rel for k in required_keys):
                        skipped_count += 1
                        continue
                    
                    head_label = rel.get('head_label')
                    tail_label = rel.get('tail_label')
                    head_name = rel.get('head')
                    tail_name = rel.get('tail')
                    relation = rel.get('relation')

                    if not all([
                        isinstance(head_label, str) and head_label.strip(),
                        isinstance(tail_label, str) and tail_label.strip(),
                        isinstance(head_name, str) and head_name.strip(),
                        isinstance(tail_name, str) and tail_name.strip(),
                        isinstance(relation, str) and relation.strip()
                    ]):
                        skipped_count += 1
                        continue

                    record_data = {
                        "head_name": head_name,
                        "head_labels": get_all_labels(head_label),
                        "tail_name": tail_name,
                        "tail_labels": get_all_labels(tail_label),
                        "rel_type": relation.upper(),
                        "rel_props": flatten_properties(rel.get('properties', {})) # <-- FLATTENING STEP
                    }
                    batch.append(record_data)

                    if len(batch) >= batch_size:
                        session.run(cypher_query, batch=batch)
                        processed_count += len(batch)
                        batch = []
                
                if batch:
                    session.run(cypher_query, batch=batch)
                    processed_count += len(batch)

    except Exception as e:
        print(f"An error occurred during processing: {e}")
    finally:
        driver.close()
        print("Database connection closed.")
        print(f"\n--- Population Complete ---")
        print(f"Total relationships successfully processed: {processed_count}")
        print(f"Total malformed relationships skipped: {skipped_count}")

if __name__ == "__main__":
    with GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD)) as driver:
        with driver.session(database="neo4j") as session:
            print("Clearing existing database for a clean run...")
            session.run("MATCH (n) DETACH DELETE n")
            print("Database cleared.")
    
    populate_graph()