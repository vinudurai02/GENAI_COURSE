# ============================================================
# 1. IMPORTS
# ============================================================

import os
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase
from langchain_openai import OpenAIEmbeddings


# ============================================================
# 2. PROJECT PATH
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent


# ============================================================
# 3. LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv(
    PROJECT_ROOT / ".env"
)

OPENAI_API_KEY = os.getenv(
    "OPENAI_API_KEY"
)

OPENAI_EMBEDDING_MODEL = os.getenv(
    "OPENAI_EMBEDDING_MODEL",
    "text-embedding-3-small"
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
# 4. VALIDATE CONFIGURATION
# ============================================================

required_variables = {
    "OPENAI_API_KEY": OPENAI_API_KEY,
    "NEO4J_URI": NEO4J_URI,
    "NEO4J_USERNAME": NEO4J_USERNAME,
    "NEO4J_PASSWORD": NEO4J_PASSWORD,
}

for variable_name, variable_value in required_variables.items():

    if not variable_value:

        raise ValueError(
            f"{variable_name} not found in .env"
        )


# ============================================================
# 5. INITIALIZE EMBEDDING MODEL
# ============================================================

embeddings = OpenAIEmbeddings(
    model=OPENAI_EMBEDDING_MODEL
)


# ============================================================
# 6. INITIALIZE NEO4J DRIVER
# ============================================================

driver = GraphDatabase.driver(
    NEO4J_URI,
    auth=(
        NEO4J_USERNAME,
        NEO4J_PASSWORD
    )
)


# ============================================================
# 7. VECTOR SEARCH
# ============================================================

def vector_search(
    question,
    top_k=3
):
    """
    Convert the user's question into an embedding
    and search the Neo4j vector index.

    Returns the most semantically relevant chunks
    and the Scheme connected to each chunk.
    """

    # --------------------------------------------------------
    # Convert question into vector
    # --------------------------------------------------------

    query_embedding = (
        embeddings.embed_query(
            question
        )
    )

    # --------------------------------------------------------
    # Search Neo4j vector index
    # --------------------------------------------------------

    query = """
    CALL db.index.vector.queryNodes(
        'scheme_chunk_embeddings',
        $top_k,
        $query_embedding
    )

    YIELD node, score

    MATCH (scheme:Scheme)-[:HAS_CHUNK]->(node)

    RETURN
        scheme.name AS scheme_name,
        scheme.description AS scheme_description,
        scheme.source_url AS source_url,
        node.id AS chunk_id,
        node.chunk_index AS chunk_index,
        node.text AS chunk_text,
        score

    ORDER BY score DESC
    """

    records, _, _ = driver.execute_query(
        query,
        top_k=top_k,
        query_embedding=query_embedding,
        database_=NEO4J_DATABASE
    )

    results = []

    for record in records:

        results.append(
            {
                "scheme_name":
                    record["scheme_name"],

                "scheme_description":
                    record["scheme_description"],

                "source_url":
                    record["source_url"],

                "chunk_id":
                    record["chunk_id"],

                "chunk_index":
                    record["chunk_index"],

                "chunk_text":
                    record["chunk_text"],

                "score":
                    record["score"],
            }
        )

    return results


# ============================================================
# 8. GET UNIQUE SCHEMES FROM VECTOR RESULTS
# ============================================================

def get_unique_scheme_names(
    vector_results
):
    """
    Vector search can return multiple chunks from
    the same Scheme.

    Example:

    Chunk 0 -> Kalaignarin
    Chunk 1 -> Kalaignarin
    Chunk 2 -> Kalaignarin

    We only need to graph-expand that Scheme once.
    """

    scheme_names = []

    for result in vector_results:

        scheme_name = result[
            "scheme_name"
        ]

        if scheme_name not in scheme_names:

            scheme_names.append(
                scheme_name
            )

    return scheme_names


# ============================================================
# 9. GRAPH EXPANSION
# ============================================================

def graph_expand(
    scheme_names
):
    """
    Starting from the Schemes discovered by vector
    search, traverse their outgoing relationships.

    This retrieves structured graph knowledge such
    as benefits, eligibility, beneficiaries,
    documents, locations, activities and department.
    """

    if not scheme_names:

        return []

    query = """
    MATCH (s:Scheme)

    WHERE s.name IN $scheme_names

    OPTIONAL MATCH (s)-[r]->(connected)

    WHERE type(r) <> 'HAS_CHUNK'

    RETURN
        s.name AS scheme_name,
        s.description AS description,
        s.scheme_type AS scheme_type,
        s.source_url AS source_url,
        type(r) AS relationship,
        labels(connected)[0] AS node_type,
        connected.name AS value

    ORDER BY
        s.name,
        relationship,
        value
    """

    records, _, _ = driver.execute_query(
        query,
        scheme_names=scheme_names,
        database_=NEO4J_DATABASE
    )

    results = []

    for record in records:

        results.append(
            {
                "scheme_name":
                    record["scheme_name"],

                "description":
                    record["description"],

                "scheme_type":
                    record["scheme_type"],

                "source_url":
                    record["source_url"],

                "relationship":
                    record["relationship"],

                "node_type":
                    record["node_type"],

                "value":
                    record["value"],
            }
        )

    return results


# ============================================================
# 10. GROUP GRAPH KNOWLEDGE BY SCHEME
# ============================================================

def group_graph_results(
    graph_results
):
    """
    Convert flat Neo4j relationship rows into a
    cleaner dictionary for each Scheme.

    Example:

    {
        "Kalaignarin Kanavu Illam": {
            "beneficiaries": [...],
            "benefits": [...],
            "eligibility": [...]
        }
    }
    """

    grouped = {}

    relationship_mapping = {
        "OFFERED_BY": "departments",
        "TARGETS": "beneficiaries",
        "PROVIDES": "benefits",
        "REQUIRES": "eligibility",
        "REQUIRES_DOCUMENT": "documents",
        "AVAILABLE_IN": "locations",
        "SUPPORTS": "activities",
    }

    for item in graph_results:

        scheme_name = item[
            "scheme_name"
        ]

        # ----------------------------------------------------
        # Create Scheme entry if it doesn't exist
        # ----------------------------------------------------

        if scheme_name not in grouped:

            grouped[scheme_name] = {
                "description":
                    item["description"],

                "scheme_type":
                    item["scheme_type"],

                "source_url":
                    item["source_url"],

                "departments": [],
                "beneficiaries": [],
                "benefits": [],
                "eligibility": [],
                "documents": [],
                "locations": [],
                "activities": [],
            }

        relationship = item[
            "relationship"
        ]

        value = item[
            "value"
        ]

        # ----------------------------------------------------
        # Ignore relationships outside our GraphRAG schema
        # ----------------------------------------------------

        field_name = (
            relationship_mapping.get(
                relationship
            )
        )

        if (
            field_name
            and value
            and value not in grouped[
                scheme_name
            ][field_name]
        ):

            grouped[
                scheme_name
            ][field_name].append(
                value
            )

    return grouped


# ============================================================
# 11. BUILD HYBRID RETRIEVAL RESULT
# ============================================================

def hybrid_retrieve(
    question,
    top_k=3
):
    """
    Complete GraphRAG retrieval pipeline.

    Question
       ↓
    Vector Search
       ↓
    Relevant Chunks
       ↓
    Relevant Schemes
       ↓
    Graph Expansion
       ↓
    Combined Retrieval Result
    """

    # --------------------------------------------------------
    # Step A: semantic vector search
    # --------------------------------------------------------

    vector_results = vector_search(
        question=question,
        top_k=top_k
    )

    # --------------------------------------------------------
    # Step B: determine which Schemes were discovered
    # --------------------------------------------------------

    scheme_names = (
        get_unique_scheme_names(
            vector_results
        )
    )

    # --------------------------------------------------------
    # Step C: expand those Schemes through the graph
    # --------------------------------------------------------

    graph_results = graph_expand(
        scheme_names
    )

    # --------------------------------------------------------
    # Step D: organize graph results
    # --------------------------------------------------------

    grouped_graph = (
        group_graph_results(
            graph_results
        )
    )

    # --------------------------------------------------------
    # Step E: return both retrieval paths
    # --------------------------------------------------------

    return {
        "question": question,
        "vector_results": vector_results,
        "scheme_names": scheme_names,
        "graph_results": grouped_graph,
    }


# ============================================================
# 12. DISPLAY VECTOR RESULTS
# ============================================================

def display_vector_results(
    vector_results
):
    """
    Display semantic vector retrieval results.
    """

    print()
    print(
        "======================================"
    )
    print(
        "VECTOR SEARCH RESULTS"
    )
    print(
        "======================================"
    )

    for index, result in enumerate(
        vector_results,
        start=1
    ):

        print()

        print(
            f"Result #{index}"
        )

        print(
            f"Scheme: "
            f"{result['scheme_name']}"
        )

        print(
            f"Score: "
            f"{result['score']:.4f}"
        )

        print(
            f"Chunk: "
            f"{result['chunk_index']}"
        )

        preview = result[
            "chunk_text"
        ][:400]

        print(
            f"Text: "
            f"{preview}..."
        )


# ============================================================
# 13. DISPLAY GRAPH EXPANSION
# ============================================================

def display_graph_results(
    grouped_graph
):
    """
    Display graph knowledge connected to each
    Scheme discovered by vector search.
    """

    print()
    print(
        "======================================"
    )
    print(
        "KNOWLEDGE GRAPH EXPANSION"
    )
    print(
        "======================================"
    )

    for scheme_name, data in (
        grouped_graph.items()
    ):

        print()
        print(
            "--------------------------------------"
        )

        print(
            f"SCHEME: {scheme_name}"
        )

        print(
            "--------------------------------------"
        )

        print()
        print(
            f"Description:\n"
            f"{data['description']}"
        )

        # ----------------------------------------------------
        # Department
        # ----------------------------------------------------

        print()
        print(
            "Departments:"
        )

        for item in data[
            "departments"
        ]:

            print(
                f"  - {item}"
            )

        # ----------------------------------------------------
        # Beneficiaries
        # ----------------------------------------------------

        print()
        print(
            "Beneficiaries:"
        )

        for item in data[
            "beneficiaries"
        ]:

            print(
                f"  - {item}"
            )

        # ----------------------------------------------------
        # Eligibility
        # ----------------------------------------------------

        print()
        print(
            "Eligibility:"
        )

        for item in data[
            "eligibility"
        ]:

            print(
                f"  - {item}"
            )

        # ----------------------------------------------------
        # Benefits
        # ----------------------------------------------------

        print()
        print(
            "Benefits:"
        )

        for item in data[
            "benefits"
        ]:

            print(
                f"  - {item}"
            )

        # ----------------------------------------------------
        # Documents
        # ----------------------------------------------------

        print()
        print(
            "Documents:"
        )

        for item in data[
            "documents"
        ]:

            print(
                f"  - {item}"
            )

        # ----------------------------------------------------
        # Locations
        # ----------------------------------------------------

        print()
        print(
            "Locations:"
        )

        for item in data[
            "locations"
        ]:

            print(
                f"  - {item}"
            )

        # ----------------------------------------------------
        # Activities
        # ----------------------------------------------------

        print()
        print(
            "Activities:"
        )

        for item in data[
            "activities"
        ]:

            print(
                f"  - {item}"
            )

        # ----------------------------------------------------
        # Source
        # ----------------------------------------------------

        print()
        print(
            f"Source: "
            f"{data['source_url']}"
        )


# ============================================================
# 14. MAIN PROGRAM
# ============================================================

def main():

    try:

        # ----------------------------------------------------
        # Verify Neo4j connection
        # ----------------------------------------------------

        driver.verify_connectivity()

        print(
            "✓ Connected to Neo4j"
        )

        # ----------------------------------------------------
        # Ask user for natural-language question
        # ----------------------------------------------------

        print()
        print(
            "======================================"
        )
        print(
            "TN SCHEME HYBRID RETRIEVER"
        )
        print(
            "======================================"
        )

        print()

        question = input(
            "Ask a question: "
        ).strip()

        if not question:

            print(
                "No question entered."
            )

            return

        # ----------------------------------------------------
        # Run hybrid GraphRAG retrieval
        # ----------------------------------------------------

        results = hybrid_retrieve(
            question=question,
            top_k=3
        )

        # ----------------------------------------------------
        # Display vector search
        # ----------------------------------------------------

        display_vector_results(
            results[
                "vector_results"
            ]
        )

        # ----------------------------------------------------
        # Display graph expansion
        # ----------------------------------------------------

        display_graph_results(
            results[
                "graph_results"
            ]
        )

    finally:

        driver.close()

        print()
        print(
            "Neo4j connection closed."
        )


# ============================================================
# 15. RUN PROGRAM
# ============================================================

if __name__ == "__main__":
    main()