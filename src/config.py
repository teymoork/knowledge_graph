import os
from dotenv import load_dotenv

# Load environment variables from .env file.
# If a variable is already set in the environment, it will not be overwritten.
load_dotenv()

# --- Neo4j Database Configuration ---
# The URI is the connection string for the database.
# "bolt" is the protocol, "localhost" is the host, and "7687" is the port.
NEO4J_URI = "bolt://localhost:7687"
# The default user for a new Neo4j instance is "neo4j".
NEO4J_USER = "neo4j"
# The password is read from the NEO4J_PASSWORD environment variable.
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# --- Google Gemini API Configuration ---
# The API key is read from the GOOGLE_API_KEY environment variable.
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# --- Sanity Checks ---
# It's good practice to ensure that essential configuration is present.
if not NEO4J_PASSWORD:
    raise ValueError("NEO4J_PASSWORD environment variable not set.")

if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable not set.")