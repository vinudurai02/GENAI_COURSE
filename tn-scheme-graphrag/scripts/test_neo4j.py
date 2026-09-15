# ============================================================
# 1. IMPORTS
# ============================================================

import os

from dotenv import load_dotenv
from neo4j import GraphDatabase


# ============================================================
# 2. LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")


# ============================================================
# 3. CREATE NEO4J DRIVER
# ============================================================

driver = GraphDatabase.driver(
    NEO4J_URI,
    auth=(NEO4J_USERNAME, NEO4J_PASSWORD)
)


# ============================================================
# 4. VERIFY CONNECTION
# ============================================================

driver.verify_connectivity()

print("✅ Connected successfully to Neo4j!")


# ============================================================
# 5. CREATE SAMPLE KNOWLEDGE GRAPH
# ============================================================

query = """
MERGE (scheme:Scheme {
    name: "Capital Subsidy Scheme"
})

MERGE (department:Department {
    name: "MSME Department"
})

MERGE (beneficiary:Beneficiary {
    name: "Manufacturing MSME"
})

MERGE (benefit:Benefit {
    name: "Capital Subsidy"
})

MERGE (activity:Activity {
    name: "Machinery Purchase"
})

MERGE (scheme)-[:OFFERED_BY]->(department)

MERGE (scheme)-[:TARGETS]->(beneficiary)

MERGE (scheme)-[:PROVIDES]->(benefit)

MERGE (benefit)-[:SUPPORTS]->(activity)
"""


# ============================================================
# 6. RUN CYPHER QUERY
# ============================================================

driver.execute_query(
    query,
    database_=NEO4J_DATABASE
)

print("✅ Sample knowledge graph created!")


# ============================================================
# 7. CLOSE DRIVER
# ============================================================

driver.close()