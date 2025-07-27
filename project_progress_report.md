--- START FILE: project_progress_report.md ---
Project Progress Report: Farsi History Knowledge Graph
Date: July 27, 2024
Overall Status: The project has successfully navigated complex data cleaning and schema engineering phases. All foundational components are in place, and the data extraction schema has been significantly enhanced through a hybrid human-AI process. The project is now fully prepared for the main Extraction Pipeline phase.
I. Completed Milestones
Phase 1: Project & Environment Setup
Objective: To establish a clean, reproducible, and professional development environment.
Actions Taken:
Project directory initialized at /home/tkh/repos/hugging_face/knowledge_graph.
Python environment management was established using poetry, ensuring consistent dependency versions via pyproject.toml and poetry.lock.
Core libraries were installed: neo4j (database driver), google-generativeai (AI model interaction), python-dotenv (secure key management), tqdm (UI progress bars), and PyMuPDF (PDF processing).
A Git repository was initialized, and a comprehensive .gitignore file was created to exclude secrets, virtual environments, and large data files from version control.
Outcome: A robust and self-contained project structure is in place, following best practices for Python development.
Phase 2: Data Sourcing and Intensive Cleaning
Objective: To convert the source material (five PDF volumes) into a single, clean, and machine-readable plain text file.
Initial Actions & Challenges:
An initial conversion was performed using the Linux pdftotext utility.
A critical file corruption issue was immediately detected: Python scripts could only read approximately half of the resulting book.txt file, despite its apparent full size on disk. This triggered an extensive and systematic debugging process.
Deep Diagnostics & Troubleshooting:
Hypothesis 1: Simple Encoding Error. Attempts to fix the file using iconv (for UTF-16, UTF-16LE) and recode failed, proving the issue was not a standard encoding mismatch.
Hypothesis 2: Hidden Control Characters. Tools like tr and grep were used to search for legacy null characters (\x00) and End-of-File markers (\x1a). These were not found, ruling out this hypothesis.
Hypothesis 3: Corrupted File Concatenation. A low-level hexdump analysis revealed that the book.txt file had been accidentally created with incorrect content (shell scripts). This was corrected by re-running the cat command with absolute paths.
Root Cause Identification: The problem persisted even after correct concatenation. This led to the final conclusion: the pdftotext utility itself was creating fundamentally corrupted .txt files from the source PDFs.
Final Resolution:
The pdftotext workflow was completely abandoned as unreliable for this source material.
The PyMuPDF Python library was adopted for a more robust, programmatic approach.
A new script, convert_pdfs.py, was written to open each PDF, iterate through every page, and extract the text, saving it into a new, clean data/book.txt.
Outcome: This phase successfully produced a high-quality, fully readable data/book.txt file, overcoming a major technical obstacle and ensuring the integrity of our source data.
Phase 3: Graph Database Setup
Objective: To deploy and configure a running Neo4j graph database instance.
Actions Taken:
Docker Engine and Docker Compose were installed and configured on the host Linux system.
A docker-compose.yml file was authored to define the Neo4j service, specifying the image version, port mappings, and inclusion of the APOC utility plugin.
Database credentials were externalized and secured in a .env file, which is ignored by Git.
The Neo4j container was launched. Initial startup failures were diagnosed by inspecting container logs (docker logs), revealing a violation of Neo4j's default password length policy.
The issue was resolved by setting a compliant password in the .env file and restarting the container.
Outcome: A stable, persistent Neo4j database is running and accessible at http://localhost:7474, ready to be populated.
Phase 4: Advanced Schema Engineering
Objective: To design and implement a comprehensive graph schema capable of capturing the rich, nuanced information present in the historical text.
Evolution of the Schema:
Initial Definition: A foundational schema was created in src/graph_schema.py with basic node labels (Person, Location) and relationships (BORN_IN, RULED).
Manual Enrichment: The schema was manually expanded based on user requirements to include detailed categories for legal proceedings, governmental structures, and complex interpersonal events.
Collaborative Modeling: A key concept, SEXUAL_ASSAULT, was refined into a more abstract and scalable VIOLENT_ACT node, demonstrating an iterative design process.
AI-Powered Schema Discovery: A dedicated script, discover_schema.py, was created to leverage the Gemini API's analytical capabilities. This script sampled the beginning, middle, and end of the book and prompted the AI to suggest novel, meaningful relationship types.
Final Integration: The 34 high-quality relationship types suggested by the AI were reviewed, deduplicated, and integrated into the src/graph_schema.py file.
Outcome: We have produced a final, highly detailed, and hybrid (human-expert + AI-suggested) schema. This schema is uniquely tailored to the specific content of the source book, enabling a far more granular and insightful knowledge graph than a generic schema would allow.
II. Current Status & Immediate Next Steps
The project is now fully prepared to execute the main data extraction and population pipeline.
Current State:
The source data (data/book.txt) is clean and verified.
The target database (Neo4j) is running and accessible.
The extraction logic (src/extract.py) is interactive and includes robust progress-tracking.
The graph schema (src/graph_schema.py) is finalized and comprehensive.
Next Steps:
Full-Scale Extraction: Execute the poetry run python src/extract.py command and, using the interactive menu, process all chunks of the book. This will populate the data/extracted_graph.json and data/progress_stats.json files.
Graph Population: Write the src/populate.py script. This script will read the final extracted_graph.json, connect to the Neo4j database, and execute the Cypher commands needed to create all the nodes and relationships defined by our schema.
Querying & Visualization: Once the database is populated, use the Neo4j Browser to run Cypher queries, explore the graph visually, and begin analyzing the historical connections.
--- END FILE: project_progress_report.md ---
