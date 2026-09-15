# ============================================================
# 1. IMPORTS
# ============================================================

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase


# ============================================================
# 2. PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "schemes_structured.json"
)


# ============================================================
# 3. LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv(
    PROJECT_ROOT / ".env"
)

NEO4J_URI = os.getenv(
    "NEO4J_URI"
)

NEO4J_USERNAME = os.getenv(
    "NEO4J_USERNAME"
)

NEO4J_PASSWORD = os.getenv(
    "NEO4J_PASSWORD"
)

NEO4J_DATABASE = os.getenv(
    "NEO4J_DATABASE",
    "neo4j"
)


# ============================================================
# 4. VALIDATE NEO4J CONFIGURATION
# ============================================================

if not NEO4J_URI:
    raise ValueError(
        "NEO4J_URI not found in .env"
    )

if not NEO4J_USERNAME:
    raise ValueError(
        "NEO4J_USERNAME not found in .env"
    )

if not NEO4J_PASSWORD:
    raise ValueError(
        "NEO4J_PASSWORD not found in .env"
    )


# ============================================================
# 5. CREATE NEO4J DRIVER
# ============================================================

driver = GraphDatabase.driver(
    NEO4J_URI,
    auth=(
        NEO4J_USERNAME,
        NEO4J_PASSWORD
    )
)


# ============================================================
# 6. VERIFY NEO4J CONNECTION
# ============================================================

def verify_connection():
    """
    Verify that Python can connect to Neo4j.
    """

    print()
    print(
        "======================================"
    )
    print(
        "VERIFYING NEO4J CONNECTION"
    )
    print(
        "======================================"
    )

    driver.verify_connectivity()

    print(
        "✓ Connected to Neo4j"
    )


# ============================================================
# 7. LOAD STRUCTURED JSON
# ============================================================

def load_schemes():
    """
    Load graph-ready scheme data created
    by Step 12.
    """

    if not INPUT_FILE.exists():

        raise FileNotFoundError(
            f"Input file not found:\n"
            f"{INPUT_FILE}"
        )

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        schemes = json.load(
            file
        )

    print(
        f"✓ Loaded {len(schemes)} schemes"
    )

    return schemes


# ============================================================
# 8. CREATE DATABASE CONSTRAINTS
# ============================================================

def create_constraints():
    """
    Create uniqueness constraints.

    These help prevent duplicate nodes.
    """

    print()
    print(
        "======================================"
    )
    print(
        "CREATING CONSTRAINTS"
    )
    print(
        "======================================"
    )

    constraints = [

        """
        CREATE CONSTRAINT scheme_name_unique
        IF NOT EXISTS
        FOR (n:Scheme)
        REQUIRE n.name IS UNIQUE
        """,

        """
        CREATE CONSTRAINT department_name_unique
        IF NOT EXISTS
        FOR (n:Department)
        REQUIRE n.name IS UNIQUE
        """,

        """
        CREATE CONSTRAINT beneficiary_name_unique
        IF NOT EXISTS
        FOR (n:Beneficiary)
        REQUIRE n.name IS UNIQUE
        """,

        """
        CREATE CONSTRAINT benefit_name_unique
        IF NOT EXISTS
        FOR (n:Benefit)
        REQUIRE n.name IS UNIQUE
        """,

        """
        CREATE CONSTRAINT eligibility_name_unique
        IF NOT EXISTS
        FOR (n:Eligibility)
        REQUIRE n.name IS UNIQUE
        """,

        """
        CREATE CONSTRAINT document_name_unique
        IF NOT EXISTS
        FOR (n:Document)
        REQUIRE n.name IS UNIQUE
        """,

        """
        CREATE CONSTRAINT location_name_unique
        IF NOT EXISTS
        FOR (n:Location)
        REQUIRE n.name IS UNIQUE
        """,

        """
        CREATE CONSTRAINT activity_name_unique
        IF NOT EXISTS
        FOR (n:Activity)
        REQUIRE n.name IS UNIQUE
        """
    ]

    for query in constraints:

        driver.execute_query(
            query,
            database_=NEO4J_DATABASE
        )

    print(
        "✓ Constraints ready"
    )


# ============================================================
# 9. CREATE SCHEME NODE
# ============================================================

def create_scheme_node(scheme):
    """
    Create or update the main Scheme node.

    Notice that we keep the longer description
    and source information as properties rather
    than separate nodes.
    """

    query = """
    MERGE (s:Scheme {name: $scheme_name})

    SET
        s.description = $description,
        s.scheme_type = $scheme_type,
        s.source_url = $source_url

    RETURN s.name AS scheme_name
    """

    driver.execute_query(
        query,
        scheme_name=scheme.get(
            "scheme_name",
            ""
        ),
        description=scheme.get(
            "description",
            ""
        ),
        scheme_type=scheme.get(
            "scheme_type",
            ""
        ),
        source_url=scheme.get(
            "source_url",
            ""
        ),
        database_=NEO4J_DATABASE
    )


# ============================================================
# 10. CREATE DEPARTMENT RELATIONSHIP
# ============================================================

def create_department_relationship(scheme):
    """
    Scheme -> OFFERED_BY -> Department
    """

    department = scheme.get(
        "department",
        ""
    )

    if not department:
        return

    query = """
    MATCH (s:Scheme {name: $scheme_name})

    MERGE (d:Department {name: $department})

    MERGE (s)-[:OFFERED_BY]->(d)
    """

    driver.execute_query(
        query,
        scheme_name=scheme["scheme_name"],
        department=department,
        database_=NEO4J_DATABASE
    )


# ============================================================
# 11. CREATE BENEFICIARY RELATIONSHIPS
# ============================================================

def create_beneficiary_relationships(scheme):
    """
    Scheme -> TARGETS -> Beneficiary
    """

    beneficiaries = scheme.get(
        "beneficiaries",
        []
    )

    query = """
    MATCH (s:Scheme {name: $scheme_name})

    UNWIND $items AS item

    WITH s, trim(item) AS item

    WHERE item <> ''

    MERGE (b:Beneficiary {name: item})

    MERGE (s)-[:TARGETS]->(b)
    """

    driver.execute_query(
        query,
        scheme_name=scheme["scheme_name"],
        items=beneficiaries,
        database_=NEO4J_DATABASE
    )


# ============================================================
# 12. CREATE ELIGIBILITY RELATIONSHIPS
# ============================================================

def create_eligibility_relationships(scheme):
    """
    Scheme -> REQUIRES -> Eligibility
    """

    eligibility = scheme.get(
        "eligibility",
        []
    )

    query = """
    MATCH (s:Scheme {name: $scheme_name})

    UNWIND $items AS item

    WITH s, trim(item) AS item

    WHERE item <> ''

    MERGE (e:Eligibility {name: item})

    MERGE (s)-[:REQUIRES]->(e)
    """

    driver.execute_query(
        query,
        scheme_name=scheme["scheme_name"],
        items=eligibility,
        database_=NEO4J_DATABASE
    )


# ============================================================
# 13. CREATE BENEFIT RELATIONSHIPS
# ============================================================

def create_benefit_relationships(scheme):
    """
    Scheme -> PROVIDES -> Benefit
    """

    benefits = scheme.get(
        "benefits",
        []
    )

    query = """
    MATCH (s:Scheme {name: $scheme_name})

    UNWIND $items AS item

    WITH s, trim(item) AS item

    WHERE item <> ''

    MERGE (b:Benefit {name: item})

    MERGE (s)-[:PROVIDES]->(b)
    """

    driver.execute_query(
        query,
        scheme_name=scheme["scheme_name"],
        items=benefits,
        database_=NEO4J_DATABASE
    )


# ============================================================
# 14. CREATE DOCUMENT RELATIONSHIPS
# ============================================================

def create_document_relationships(scheme):
    """
    Scheme -> REQUIRES_DOCUMENT -> Document
    """

    documents = scheme.get(
        "documents_required",
        []
    )

    query = """
    MATCH (s:Scheme {name: $scheme_name})

    UNWIND $items AS item

    WITH s, trim(item) AS item

    WHERE item <> ''

    MERGE (d:Document {name: item})

    MERGE (s)-[:REQUIRES_DOCUMENT]->(d)
    """

    driver.execute_query(
        query,
        scheme_name=scheme["scheme_name"],
        items=documents,
        database_=NEO4J_DATABASE
    )


# ============================================================
# 15. CREATE LOCATION RELATIONSHIPS
# ============================================================

def create_location_relationships(scheme):
    """
    Scheme -> AVAILABLE_IN -> Location
    """

    locations = scheme.get(
        "locations",
        []
    )

    query = """
    MATCH (s:Scheme {name: $scheme_name})

    UNWIND $items AS item

    WITH s, trim(item) AS item

    WHERE item <> ''

    MERGE (l:Location {name: item})

    MERGE (s)-[:AVAILABLE_IN]->(l)
    """

    driver.execute_query(
        query,
        scheme_name=scheme["scheme_name"],
        items=locations,
        database_=NEO4J_DATABASE
    )


# ============================================================
# 16. CREATE ACTIVITY RELATIONSHIPS
# ============================================================

def create_activity_relationships(scheme):
    """
    Scheme -> SUPPORTS -> Activity
    """

    activities = scheme.get(
        "activities",
        []
    )

    query = """
    MATCH (s:Scheme {name: $scheme_name})

    UNWIND $items AS item

    WITH s, trim(item) AS item

    WHERE item <> ''

    MERGE (a:Activity {name: item})

    MERGE (s)-[:SUPPORTS]->(a)
    """

    driver.execute_query(
        query,
        scheme_name=scheme["scheme_name"],
        items=activities,
        database_=NEO4J_DATABASE
    )


# ============================================================
# 17. BUILD ONE SCHEME SUBGRAPH
# ============================================================

def build_scheme_graph(scheme):
    """
    Convert one structured JSON object
    into Neo4j nodes and relationships.
    """

    create_scheme_node(
        scheme
    )

    create_department_relationship(
        scheme
    )

    create_beneficiary_relationships(
        scheme
    )

    create_eligibility_relationships(
        scheme
    )

    create_benefit_relationships(
        scheme
    )

    create_document_relationships(
        scheme
    )

    create_location_relationships(
        scheme
    )

    create_activity_relationships(
        scheme
    )


# ============================================================
# 18. BUILD COMPLETE KNOWLEDGE GRAPH
# ============================================================

def build_knowledge_graph(schemes):
    """
    Insert every scheme into Neo4j.
    """

    print()
    print(
        "======================================"
    )
    print(
        "BUILDING KNOWLEDGE GRAPH"
    )
    print(
        "======================================"
    )
    print()

    total = len(schemes)

    successful = 0
    failed = 0

    for index, scheme in enumerate(
        schemes,
        start=1
    ):

        scheme_name = scheme.get(
            "scheme_name",
            "Unknown Scheme"
        )

        print(
            f"[{index}/{total}] "
            f"{scheme_name}"
        )

        try:

            build_scheme_graph(
                scheme
            )

            successful += 1

            print(
                "   ✓ Graph created"
            )

        except Exception as error:

            failed += 1

            print(
                f"   ❌ Failed: {error}"
            )

    return successful, failed


# ============================================================
# 19. GET GRAPH STATISTICS
# ============================================================

def get_graph_statistics():
    """
    Count nodes and relationships created
    for our graph labels.
    """

    node_query = """
    MATCH (n)

    WHERE
        n:Scheme
        OR n:Department
        OR n:Beneficiary
        OR n:Eligibility
        OR n:Benefit
        OR n:Document
        OR n:Location
        OR n:Activity

    RETURN
        labels(n)[0] AS label,
        count(n) AS count

    ORDER BY label
    """

    relationship_query = """
    MATCH (s:Scheme)-[r]->()

    RETURN
        type(r) AS relationship,
        count(r) AS count

    ORDER BY relationship
    """

    node_records, _, _ = driver.execute_query(
        node_query,
        database_=NEO4J_DATABASE
    )

    relationship_records, _, _ = (
        driver.execute_query(
            relationship_query,
            database_=NEO4J_DATABASE
        )
    )

    print()
    print(
        "======================================"
    )
    print(
        "NODE STATISTICS"
    )
    print(
        "======================================"
    )

    for record in node_records:

        print(
            f"{record['label']}: "
            f"{record['count']}"
        )

    print()
    print(
        "======================================"
    )
    print(
        "RELATIONSHIP STATISTICS"
    )
    print(
        "======================================"
    )

    for record in relationship_records:

        print(
            f"{record['relationship']}: "
            f"{record['count']}"
        )


# ============================================================
# 20. DISPLAY SAMPLE GRAPH
# ============================================================

def display_sample():
    """
    Display one scheme and the number of
    connected nodes from Python.
    """

    query = """
    MATCH (s:Scheme)-[r]->(connected)

    RETURN
        s.name AS scheme,
        type(r) AS relationship,
        labels(connected)[0] AS node_type,
        connected.name AS connected_node

    ORDER BY
        scheme,
        relationship

    LIMIT 20
    """

    records, _, _ = driver.execute_query(
        query,
        database_=NEO4J_DATABASE
    )

    print()
    print(
        "======================================"
    )
    print(
        "SAMPLE GRAPH DATA"
    )
    print(
        "======================================"
    )

    for record in records:

        print()

        print(
            f"Scheme: "
            f"{record['scheme']}"
        )

        print(
            f"Relationship: "
            f"{record['relationship']}"
        )

        print(
            f"Node Type: "
            f"{record['node_type']}"
        )

        print(
            f"Connected Node: "
            f"{record['connected_node']}"
        )


# ============================================================
# 21. MAIN PROGRAM
# ============================================================

def main():

    try:

        # ----------------------------------------------------
        # Test database connection
        # ----------------------------------------------------

        verify_connection()

        # ----------------------------------------------------
        # Load Step 12 JSON
        # ----------------------------------------------------

        schemes = load_schemes()

        # ----------------------------------------------------
        # Create constraints
        # ----------------------------------------------------

        create_constraints()

        # ----------------------------------------------------
        # Build graph
        # ----------------------------------------------------

        successful, failed = (
            build_knowledge_graph(
                schemes
            )
        )

        # ----------------------------------------------------
        # Show database statistics
        # ----------------------------------------------------

        get_graph_statistics()

        # ----------------------------------------------------
        # Show sample data
        # ----------------------------------------------------

        display_sample()

        # ----------------------------------------------------
        # Final summary
        # ----------------------------------------------------

        print()
        print(
            "======================================"
        )
        print(
            "GRAPH BUILD SUMMARY"
        )
        print(
            "======================================"
        )

        print(
            f"Successful schemes: "
            f"{successful}"
        )

        print(
            f"Failed schemes: "
            f"{failed}"
        )

    finally:

        # ----------------------------------------------------
        # Always close Neo4j connection
        # ----------------------------------------------------

        driver.close()

        print()
        print(
            "Neo4j connection closed."
        )


# ============================================================
# 22. RUN PROGRAM
# ============================================================

if __name__ == "__main__":
    main()