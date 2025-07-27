import ijson
from neo4j import GraphDatabase
from tqdm import tqdm
import config
from graph_schema import NodeLabel, RelationshipLabel, POSSIBLE_RELATIONSHIPS

# --- Configuration ---
GRAPH_JSON_PATH = "data/extracted_graph.json"
BATCH_SIZE = 1000  # Process 1000 triplets per transaction for better performance

# Create a mapping from relationship labels to the expected node labels for head and tail
RELATIONSHIP_TO_NODE_LABELS = {}
for head_label, rel_label, tail_label in POSSIBLE_RELATIONSHIPS:
    RELATIONSHIP_TO_NODE_LABELS[rel_label.value] = {
        "head": head_label.value,
        "tail": tail_label.value
    }

def get_node_labels(relation: str) -> tuple[str, str] | None:
    """Looks up the correct node labels for a given relationship."""
    rule = RELATIONSHIP_TO_NODE_LABELS.get(relation)
    if not rule:
        return None
    return rule["head"], rule["tail"]

def main():
    """
    Populates the Neo4j database from the extracted_graph.json file.
    """
    print("--- Starting Neo4j Database Population ---")
    
    try:
        driver = GraphDatabase.driver(
            config.NEO4J_URI, 
            auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
        )
        driver.verify_connectivity()
        print("Successfully connected to Neo4j database.")
    except Exception as e:
        print(f"Error: Could not connect to Neo4j. Please ensure the database is running. Details: {e}")
        return

    with driver.session() as session:
        print("Ensuring database constraints exist...")
        for label in NodeLabel:
            session.run(f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:`{label.value}`) REQUIRE n.name IS UNIQUE")
        print("Constraints are in place.")

        triplets_batch = []
        processed_count = 0

        print(f"Streaming and processing triplets from {GRAPH_JSON_PATH}...")
        try:
            with open(GRAPH_JSON_PATH, 'rb') as f:
                # --- CORRECTED LINE ---
                # Look for items under the 'graph' key at the root, then iterate its items.
                json_stream = ijson.items(f, 'graph.item')
                
                for triplet in tqdm(json_stream, desc="Populating database"):
                    if not all(key in triplet for key in ["head", "relation", "tail"]):
                        tqdm.write(f"Skipping malformed triplet: {triplet}")
                        continue
                    
                    triplets_batch.append(triplet)

                    if len(triplets_batch) >= BATCH_SIZE:
                        process_batch(session, triplets_batch)
                        processed_count += len(triplets_batch)
                        triplets_batch = []
                
                if triplets_batch:
                    process_batch(session, triplets_batch)
                    processed_count += len(triplets_batch)

        except FileNotFoundError:
            print(f"ERROR: The file {GRAPH_JSON_PATH} was not found. Please run the extraction script first.")
            driver.close()
            return
        except Exception as e:
            print(f"An error occurred while reading the JSON file: {e}")
            driver.close()
            return

    print(f"\n--- Population Complete ---")
    print(f"Successfully processed and merged {processed_count} triplets into the database.")
    driver.close()

def process_batch(session, batch: list[dict]):
    """
    Processes a batch of triplets in a single transaction.
    """
    cypher_query = """
    UNWIND $triplets AS triplet
    
    WITH triplet,
         apoc.map.get($label_map, triplet.relation, null, false) AS labels
    WHERE labels IS NOT NULL

    CALL apoc.merge.node([labels.head], {name: triplet.head}) YIELD node AS headNode
    
    CALL apoc.merge.node([labels.tail], {name: triplet.tail}) YIELD node AS tailNode
    
    CALL apoc.merge.relationship(headNode, triplet.relation, {}, {}, tailNode) YIELD rel
    
    RETURN count(*)
    """
    
    session.run(cypher_query, triplets=batch, label_map=RELATIONSHIP_TO_NODE_LABELS)

if __name__ == "__main__":
    main()