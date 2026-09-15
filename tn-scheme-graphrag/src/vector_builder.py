# ============================================================
# 1. IMPORTS
# ============================================================

import json
import os
import hashlib
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter


# ============================================================
# 2. PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "schemes_detailed.json"
)


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
# 5. INITIALIZE NEO4J DRIVER
# ============================================================

driver = GraphDatabase.driver(
    NEO4J_URI,
    auth=(
        NEO4J_USERNAME,
        NEO4J_PASSWORD
    )
)


# ============================================================
# 6. INITIALIZE OPENAI EMBEDDINGS
# ============================================================

embeddings = OpenAIEmbeddings(
    model=OPENAI_EMBEDDING_MODEL
)


# ============================================================
# 7. TEXT SPLITTER
# ============================================================

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=150,
    separators=[
        "\n\n",
        "\n",
        ". ",
        " ",
        ""
    ]
)


# ============================================================
# 8. LOAD DETAILED SOURCE DOCUMENTS
# ============================================================

def load_documents():
    """
    Load the original cleaned government scheme
    content created during Step 11.

    We use schemes_detailed.json instead of the
    LLM-generated structured JSON because we want
    embeddings from the original source evidence.
    """

    if not INPUT_FILE.exists():

        raise FileNotFoundError(
            f"Input file not found:\n{INPUT_FILE}"
        )

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        documents = json.load(
            file
        )

    print(
        f"✓ Loaded {len(documents)} source documents"
    )

    return documents


# ============================================================
# 9. CREATE STABLE CHUNK ID
# ============================================================

def create_chunk_id(
    scheme_name,
    chunk_index,
    chunk_text
):
    """
    Create a stable unique ID for each chunk.

    This helps MERGE avoid duplicate chunks when
    the script is run again.
    """

    value = (
        f"{scheme_name}|"
        f"{chunk_index}|"
        f"{chunk_text}"
    )

    return hashlib.sha256(
        value.encode("utf-8")
    ).hexdigest()


# ============================================================
# 10. SPLIT ONE SCHEME INTO CHUNKS
# ============================================================

def create_chunks(document):
    """
    Split one government scheme document
    into smaller text chunks.
    """

    raw_content = document.get(
        "raw_content",
        ""
    )

    if not raw_content.strip():

        return []

    chunks = text_splitter.split_text(
        raw_content
    )

    return chunks


# ============================================================
# 11. CREATE CHUNK CONSTRAINT
# ============================================================

def create_chunk_constraint():
    """
    Prevent duplicate Chunk IDs.
    """

    query = """
    CREATE CONSTRAINT chunk_id_unique
    IF NOT EXISTS
    FOR (c:Chunk)
    REQUIRE c.id IS UNIQUE
    """

    driver.execute_query(
        query,
        database_=NEO4J_DATABASE
    )

    print(
        "✓ Chunk uniqueness constraint ready"
    )


# ============================================================
# 12. STORE CHUNK IN NEO4J
# ============================================================

def store_chunk(
    scheme_name,
    source_url,
    chunk_id,
    chunk_index,
    chunk_text,
    embedding
):
    """
    Create a Chunk node, store its embedding,
    and connect it to the Scheme node.
    """

    query = """
    MATCH (s:Scheme {name: $scheme_name})

    MERGE (c:Chunk {id: $chunk_id})

    SET
        c.text = $chunk_text,
        c.chunk_index = $chunk_index,
        c.source_url = $source_url,
        c.embedding = $embedding

    MERGE (s)-[:HAS_CHUNK]->(c)

    RETURN c.id AS chunk_id
    """

    records, _, _ = driver.execute_query(
        query,
        scheme_name=scheme_name,
        source_url=source_url,
        chunk_id=chunk_id,
        chunk_index=chunk_index,
        chunk_text=chunk_text,
        embedding=embedding,
        database_=NEO4J_DATABASE
    )

    if not records:

        raise ValueError(
            f"Scheme not found in Neo4j: {scheme_name}"
        )


# ============================================================
# 13. PROCESS ONE SCHEME
# ============================================================

def process_scheme(document):
    """
    Chunk one scheme, create embeddings,
    and store everything in Neo4j.
    """

    scheme_name = document.get(
        "scheme_name",
        ""
    )

    source_url = document.get(
        "detail_url",
        ""
    )

    chunks = create_chunks(
        document
    )

    if not chunks:

        print(
            "   ⚠️ No chunks created"
        )

        return 0

    print(
        f"   Chunks: {len(chunks)}"
    )

    # --------------------------------------------------------
    # Embed all chunks for this scheme in one API request
    # --------------------------------------------------------

    chunk_embeddings = (
        embeddings.embed_documents(
            chunks
        )
    )

    # --------------------------------------------------------
    # Store each chunk + embedding in Neo4j
    # --------------------------------------------------------

    for chunk_index, (
        chunk_text,
        embedding
    ) in enumerate(
        zip(
            chunks,
            chunk_embeddings
        )
    ):

        chunk_id = create_chunk_id(
            scheme_name,
            chunk_index,
            chunk_text
        )

        store_chunk(
            scheme_name=scheme_name,
            source_url=source_url,
            chunk_id=chunk_id,
            chunk_index=chunk_index,
            chunk_text=chunk_text,
            embedding=embedding
        )

    return len(chunks)


# ============================================================
# 14. PROCESS ALL SCHEMES
# ============================================================

def build_vectors(documents):
    """
    Create chunks and embeddings for all
    scraped government scheme documents.
    """

    print()
    print(
        "======================================"
    )
    print(
        "BUILDING CHUNKS AND EMBEDDINGS"
    )
    print(
        "======================================"
    )
    print()

    total_chunks = 0
    successful = 0
    failed = 0

    for index, document in enumerate(
        documents,
        start=1
    ):

        scheme_name = document.get(
            "scheme_name",
            "Unknown Scheme"
        )

        print(
            f"[{index}/{len(documents)}] "
            f"{scheme_name}"
        )

        try:

            chunk_count = process_scheme(
                document
            )

            total_chunks += chunk_count
            successful += 1

            print(
                "   ✓ Embeddings stored"
            )

        except Exception as error:

            failed += 1

            print(
                f"   ❌ Failed: {error}"
            )

        print()

    return (
        successful,
        failed,
        total_chunks
    )


# ============================================================
# 15. DETECT EMBEDDING DIMENSIONS
# ============================================================

def get_embedding_dimensions():
    """
    Ask the configured embedding model for one
    embedding so we know the vector dimensions.

    This avoids hardcoding the vector size.
    """

    test_embedding = (
        embeddings.embed_query(
            "Tamil Nadu government scheme"
        )
    )

    dimensions = len(
        test_embedding
    )

    print(
        f"✓ Embedding dimensions: {dimensions}"
    )

    return dimensions


# ============================================================
# 16. CREATE NEO4J VECTOR INDEX
# ============================================================

def create_vector_index(dimensions):
    """
    Create a Neo4j vector index on Chunk.embedding.
    """

    query = f"""
    CREATE VECTOR INDEX scheme_chunk_embeddings
    IF NOT EXISTS

    FOR (c:Chunk)

    ON c.embedding

    OPTIONS {{
        indexConfig: {{
            `vector.dimensions`: {dimensions},
            `vector.similarity_function`: 'cosine'
        }}
    }}
    """

    driver.execute_query(
        query,
        database_=NEO4J_DATABASE
    )

    print(
        "✓ Neo4j vector index ready"
    )


# ============================================================
# 17. VERIFY CHUNKS
# ============================================================

def verify_chunks():
    """
    Verify that Chunk nodes and embeddings
    exist in Neo4j.
    """

    query = """
    MATCH (s:Scheme)-[:HAS_CHUNK]->(c:Chunk)

    RETURN
        count(c) AS chunk_count,
        count(c.embedding) AS embedded_chunks
    """

    records, _, _ = driver.execute_query(
        query,
        database_=NEO4J_DATABASE
    )

    if records:

        print()
        print(
            "======================================"
        )
        print(
            "VECTOR STATISTICS"
        )
        print(
            "======================================"
        )

        print(
            f"Chunks: "
            f"{records[0]['chunk_count']}"
        )

        print(
            f"Chunks with embeddings: "
            f"{records[0]['embedded_chunks']}"
        )


# ============================================================
# 18. TEST VECTOR SEARCH
# ============================================================

def test_vector_search():
    """
    Perform our first semantic vector search.

    Notice that the query is natural language,
    not an exact keyword search.
    """

    question = (
        "I live in a hut and need help "
        "building a permanent house"
    )

    query_embedding = (
        embeddings.embed_query(
            question
        )
    )

    query = """
    CALL db.index.vector.queryNodes(
        'scheme_chunk_embeddings',
        3,
        $query_embedding
    )

    YIELD node, score

    MATCH (s:Scheme)-[:HAS_CHUNK]->(node)

    RETURN
        s.name AS scheme,
        score,
        node.chunk_index AS chunk_index,
        node.text AS text

    ORDER BY score DESC
    """

    records, _, _ = driver.execute_query(
        query,
        query_embedding=query_embedding,
        database_=NEO4J_DATABASE
    )

    print()
    print(
        "======================================"
    )
    print(
        "TEST VECTOR SEARCH"
    )
    print(
        "======================================"
    )

    print(
        f"Question: {question}"
    )

    for record in records:

        print()
        print(
            f"Scheme: "
            f"{record['scheme']}"
        )

        print(
            f"Score: "
            f"{record['score']:.4f}"
        )

        print(
            f"Chunk: "
            f"{record['chunk_index']}"
        )

        preview = record[
            "text"
        ][:300]

        print(
            f"Text: "
            f"{preview}..."
        )


# ============================================================
# 19. MAIN PROGRAM
# ============================================================

def main():

    try:

        # ----------------------------------------------------
        # Verify Neo4j
        # ----------------------------------------------------

        driver.verify_connectivity()

        print(
            "✓ Connected to Neo4j"
        )

        # ----------------------------------------------------
        # Load original government documents
        # ----------------------------------------------------

        documents = load_documents()

        # ----------------------------------------------------
        # Create Chunk constraint
        # ----------------------------------------------------

        create_chunk_constraint()

        # ----------------------------------------------------
        # Determine embedding dimensions
        # ----------------------------------------------------

        dimensions = (
            get_embedding_dimensions()
        )

        # ----------------------------------------------------
        # Build chunks + embeddings
        # ----------------------------------------------------

        (
            successful,
            failed,
            total_chunks
        ) = build_vectors(
            documents
        )

        # ----------------------------------------------------
        # Create vector index
        # ----------------------------------------------------

        create_vector_index(
            dimensions
        )

        # ----------------------------------------------------
        # Verify stored vectors
        # ----------------------------------------------------

        verify_chunks()

        # ----------------------------------------------------
        # Test semantic search
        # ----------------------------------------------------

        test_vector_search()

        # ----------------------------------------------------
        # Final summary
        # ----------------------------------------------------

        print()
        print(
            "======================================"
        )
        print(
            "VECTOR BUILD SUMMARY"
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

        print(
            f"Chunks processed: "
            f"{total_chunks}"
        )

    finally:

        driver.close()

        print()
        print(
            "Neo4j connection closed."
        )


# ============================================================
# 20. RUN PROGRAM
# ============================================================

if __name__ == "__main__":
    main()