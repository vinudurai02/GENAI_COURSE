"""
=============================================================================
 Simple Knowledge Graph RAG (Retrieval-Augmented Generation)
=============================================================================

 WHAT THIS DOES:
 1. Reads FAQ.txt (question-answer pairs)
 2. Pushes them into Neo4j Aura DB as a Knowledge Graph
 3. Lets you ask questions interactively
 4. Retrieves relevant answers from the graph + uses OpenAI to generate response

 ARCHITECTURE (Simple View):

   FAQ.txt --> [Parse] --> [Neo4j Graph DB] --> [Retrieve] --> [OpenAI LLM] --> Answer
                              (nodes &                          (generates
                             relationships)                    natural response)

 GRAPH STRUCTURE:
   (Topic) --[:HAS_FAQ]--> (FAQ) --[:HAS_ANSWER]--> (Answer)

   Example:
   (Python) --[:HAS_FAQ]--> ("What is Python?") --[:HAS_ANSWER]--> ("Python is a...")

=============================================================================
"""

import os
import re
from dotenv import load_dotenv
from neo4j import GraphDatabase
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate


# ─────────────────────────────────────────────────
# STEP 1: Load environment variables from .env file
# ─────────────────────────────────────────────────
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# Quick check: make sure all keys are set
for var_name in ["OPENAI_API_KEY", "NEO4J_URI", "NEO4J_USERNAME", "NEO4J_PASSWORD"]:
    if not os.getenv(var_name):
        raise ValueError(f"Missing {var_name} in .env file. See .env.example")


# ─────────────────────────────────────────────────
# STEP 2: Parse the FAQ.txt file
# ─────────────────────────────────────────────────
# We read FAQ.txt and extract (question, answer) pairs.
# Each Q: line starts a question, each A: line starts its answer.

def parse_faq(file_path: str) -> list[dict]:
    """
    Reads FAQ.txt and returns a list of dicts:
      [{"question": "What is Python?", "answer": "Python is..."}, ...]
    """
    faqs = []
    with open(file_path, "r") as f:
        content = f.read()

    # Split by "Q:" to get each QA block
    blocks = content.split("Q: ")

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        # Split each block into question and answer
        if "A: " in block:
            parts = block.split("A: ", 1)  # split only on first "A: "
            question = parts[0].strip()
            answer = parts[1].strip()
            faqs.append({"question": question, "answer": answer})

    print(f"Parsed {len(faqs)} FAQ entries from {file_path}")
    return faqs


# ─────────────────────────────────────────────────
# STEP 3: Connect to Neo4j and push FAQs as a graph
# ─────────────────────────────────────────────────
# We create 3 types of nodes:
#   - Topic  : the main subject (extracted from the question)
#   - FAQ    : the question itself
#   - Answer : the answer text
#
# And 2 relationships:
#   - (Topic) -[:HAS_FAQ]-> (FAQ)
#   - (FAQ) -[:HAS_ANSWER]-> (Answer)

def extract_topic(question: str) -> str:
    """
    Simple topic extraction from a question.
    e.g., "What is Python?" --> "Python"
    e.g., "What is a Knowledge Graph?" --> "Knowledge Graph"
    """
    # Remove "What is" / "What is a" / "What is an" and the "?"
    topic = question
    for prefix in ["What is an ", "What is a ", "What is "]:
        if topic.startswith(prefix):
            topic = topic[len(prefix):]
            break
    topic = topic.rstrip("?").strip()
    return topic


def clear_graph(driver):
    """Delete all existing nodes and relationships (clean start)."""
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")
    print("Cleared existing graph data.")


def push_faqs_to_graph(driver, faqs: list[dict]):
    """
    Creates nodes and relationships in Neo4j for each FAQ.

    Cypher query explanation:
      MERGE = create if not exists (avoids duplicates)
      CREATE = always create new node
    """
    with driver.session() as session:
        for faq in faqs:
            topic = extract_topic(faq["question"])

            # This Cypher query creates:
            #   (Topic node) --> (FAQ node) --> (Answer node)
            cypher = """
                MERGE (t:Topic {name: $topic})
                CREATE (q:FAQ {question: $question})
                CREATE (a:Answer {text: $answer})
                CREATE (t)-[:HAS_FAQ]->(q)
                CREATE (q)-[:HAS_ANSWER]->(a)
            """
            session.run(
                cypher,
                topic=topic,
                question=faq["question"],
                answer=faq["answer"],
            )

    print(f"Pushed {len(faqs)} FAQs to Neo4j Knowledge Graph!")


# ─────────────────────────────────────────────────
# STEP 4: Retrieve relevant answers from the graph
# ─────────────────────────────────────────────────
# When the user asks a question, we search the graph
# for FAQ nodes whose question text contains keywords
# from the user's query.

def search_graph(driver, user_query: str) -> list[dict]:
    """
    Searches Neo4j for FAQs related to the user's query.

    Strategy: extract keywords from the query, then search
    for FAQ nodes whose question contains those keywords.
    Returns matching question-answer pairs.
    """
    # Extract meaningful words (ignore short/common words)
    stop_words = {"what", "is", "a", "an", "the", "how", "does", "do", "can",
                  "tell", "me", "about", "explain", "define", "i", "want",
                  "to", "know", "of", "in", "for", "and", "or", "it"}
    words = re.findall(r'\w+', user_query.lower())
    keywords = [w for w in words if w not in stop_words and len(w) > 1]

    if not keywords:
        # Fallback: use all words longer than 2 chars
        keywords = [w for w in words if len(w) > 2]

    results = []
    with driver.session() as session:
        for keyword in keywords:
            # Cypher: find FAQ nodes where the question contains our keyword
            # toLower() makes it case-insensitive
            cypher = """
                MATCH (t:Topic)-[:HAS_FAQ]->(q:FAQ)-[:HAS_ANSWER]->(a:Answer)
                WHERE toLower(q.question) CONTAINS toLower($keyword)
                   OR toLower(t.name) CONTAINS toLower($keyword)
                RETURN t.name AS topic, q.question AS question, a.text AS answer
            """
            records = session.run(cypher, keyword=keyword)
            for record in records:
                entry = {
                    "topic": record["topic"],
                    "question": record["question"],
                    "answer": record["answer"],
                }
                # Avoid duplicates
                if entry not in results:
                    results.append(entry)

    return results


# ─────────────────────────────────────────────────
# STEP 5: Use OpenAI LLM to generate a nice answer
# ─────────────────────────────────────────────────
# We take the retrieved graph data and pass it to OpenAI
# along with the user's question. The LLM generates a
# natural language response grounded in the graph data.

def create_rag_chain():
    """
    Creates a LangChain LLM chain with a prompt template.

    The prompt tells the LLM:
      - Here is context from our Knowledge Graph
      - Answer the user's question using ONLY this context
      - If context is empty, say you don't know
    """
    # Initialize OpenAI LLM via LangChain
    llm = ChatOpenAI(
        model="gpt-4o-mini",       # affordable & capable model
        temperature=0,              # 0 = deterministic (no creativity)
        openai_api_key=OPENAI_API_KEY,
    )

    # The prompt template -- this is the "instruction" to the LLM
    prompt = PromptTemplate(
        input_variables=["context", "question"],
        template="""You are a helpful assistant that answers questions using
ONLY the context provided from a Knowledge Graph.

=== Knowledge Graph Context ===
{context}
================================

User Question: {question}

Instructions:
- Answer based ONLY on the context above.
- If the context is empty or doesn't contain relevant info, say:
  "I don't have information about that in my knowledge graph."
- Keep the answer clear and concise.
- If multiple topics are relevant, mention all of them.

Answer:""",
    )

    # Create the chain: prompt | LLM (pipe operator connects them)
    # This is the modern LangChain way (LCEL - LangChain Expression Language)
    chain = prompt | llm
    return chain


def ask_question(driver, chain, user_question: str) -> str:
    """
    Full RAG pipeline:
      1. Search the Knowledge Graph for relevant data
      2. Format the results as context
      3. Pass context + question to LLM
      4. Return the LLM's answer
    """
    # Step A: Retrieve from graph
    results = search_graph(driver, user_question)

    # Step B: Format results into a readable context string
    if results:
        context_parts = []
        for r in results:
            context_parts.append(
                f"Topic: {r['topic']}\n"
                f"Question: {r['question']}\n"
                f"Answer: {r['answer']}"
            )
        context = "\n\n".join(context_parts)
    else:
        context = "(No relevant information found in the Knowledge Graph)"

    # Show what was retrieved (for learning/debugging)
    print(f"\n  [Graph Search] Found {len(results)} relevant entries")

    # Step C: Send to LLM and get response
    # chain.invoke() returns an AIMessage object; .content gets the text
    response = chain.invoke({
        "context": context,
        "question": user_question,
    })

    return response.content


# ─────────────────────────────────────────────────
# STEP 6: Main -- tie it all together
# ─────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  Simple Knowledge Graph RAG")
    print("  (LangChain + Neo4j + OpenAI)")
    print("=" * 60)

    # --- Connect to Neo4j ---
    print("\n[1/3] Connecting to Neo4j Aura DB...")
    print(f"  URI: {NEO4J_URI}")
    if "xxxxxxxx" in NEO4J_URI:
        print("\n  ERROR: You still have the placeholder URI in your .env file!")
        print("  Go to https://console.neo4j.io, click your instance,")
        print("  and copy the 'Connection URI' into NEO4J_URI in .env")
        return
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    try:
        driver.verify_connectivity()
    except Exception as e:
        print(f"\n  ERROR: Could not connect to Neo4j: {e}")
        print("\n  Checklist:")
        print("  1. Is your Neo4j Aura instance running? (check console.neo4j.io)")
        print("  2. Is NEO4J_URI correct? (should look like neo4j+s://xxxx.databases.neo4j.io)")
        print("  3. Is NEO4J_USERNAME correct? (usually 'neo4j' for Aura)")
        print("  4. Is NEO4J_PASSWORD correct?")
        driver.close()
        return
    print("  Connected successfully!")

    # --- Parse and push FAQs ---
    print("\n[2/3] Loading FAQ.txt into Knowledge Graph...")
    faq_file = os.path.join(os.path.dirname(__file__), "FAQ.txt")
    faqs = parse_faq(faq_file)
    clear_graph(driver)
    push_faqs_to_graph(driver, faqs)

    # --- Create RAG chain ---
    print("\n[3/3] Setting up RAG chain (LangChain + OpenAI)...")
    chain = create_rag_chain()
    print("  Ready!\n")

    # --- Interactive Q&A Loop ---
    print("=" * 60)
    print("  Ask me anything about the FAQ topics!")
    print("  Type 'quit' or 'exit' to stop.")
    print("=" * 60)

    while True:
        print()
        user_input = input("You: ").strip()

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print("\nGoodbye!")
            break

        answer = ask_question(driver, chain, user_input)
        print(f"\nAssistant: {answer}")

    # Cleanup
    driver.close()


if __name__ == "__main__":
    main()