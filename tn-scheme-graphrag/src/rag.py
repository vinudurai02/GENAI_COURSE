# ============================================================
# 1. IMPORTS
# ============================================================

import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from retriever import (
    hybrid_retrieve,
    driver
)


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

OPENAI_CHAT_MODEL = os.getenv(
    "OPENAI_CHAT_MODEL",
    "gpt-5-mini"
)


# ============================================================
# 4. VALIDATE CONFIGURATION
# ============================================================

if not OPENAI_API_KEY:

    raise ValueError(
        "OPENAI_API_KEY not found in .env"
    )


# ============================================================
# 5. INITIALIZE CHAT MODEL
# ============================================================

llm = ChatOpenAI(
    model=OPENAI_CHAT_MODEL,
    temperature=0
)


# ============================================================
# 6. QUESTION REWRITER PROMPT
# ============================================================

question_rewriter_prompt = (
    ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
You rewrite follow-up questions for a Tamil Nadu
Government scheme retrieval system.

Your task is to convert the user's latest question
into a complete standalone search question using
the supplied conversation history.

RULES:

1. Preserve the user's original meaning.

2. Use conversation history only when necessary.

3. Resolve references such as:
   - it
   - this scheme
   - that scheme
   - this
   - they
   - those benefits
   - what documents
   - how much
   - am I eligible

4. Do not answer the question.

5. Do not add facts that were not present in the
   conversation.

6. If the latest question is already standalone,
   return it essentially unchanged.

7. Return ONLY the rewritten question.

Example:

Conversation:
User: Tell me about Kalaignarin Kanavu Illam.
Assistant: Kalaignarin Kanavu Illam is a rural
housing scheme...

Latest question:
What documents are required?

Output:
What documents are required for Kalaignarin
Kanavu Illam?
"""
            ),
            (
                "human",
                """
CONVERSATION HISTORY:

{chat_history}


LATEST QUESTION:

{question}


Rewrite the latest question as a standalone
retrieval question.
"""
            )
        ]
    )
)


# ============================================================
# 7. FINAL ANSWER PROMPT
# ============================================================

answer_prompt = (
    ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
You are an assistant for Tamil Nadu Government schemes.

Answer the user's question using ONLY:

1. The retrieved original government source evidence.
2. The retrieved knowledge graph information.
3. The conversation history only for understanding
   conversational context.

IMPORTANT RULES:

1. Do not use outside knowledge.

2. Do not invent scheme details.

3. If the retrieved evidence is insufficient,
   clearly say so.

4. Prefer the original government source evidence
   if there is any conflict with extracted graph
   information.

5. Use graph information when relevant to explain:
   - scheme name
   - beneficiaries
   - eligibility
   - benefits
   - documents
   - locations
   - activities

6. Never tell the user they are definitely eligible
   unless the supplied evidence establishes it.

7. Clearly distinguish between:
   - information supplied by the user
   - general scheme requirements

8. Do not fabricate application procedures,
   offices, phone numbers, deadlines, websites,
   documents or other information.

9. Keep the answer practical and easy to understand.

10. Mention the relevant scheme name.

11. Include a short Source section using the
    supplied source URL.

12. If multiple schemes are relevant, explain
    them separately.

13. Conversation history helps you understand the
    dialogue, but it is NOT authoritative government
    evidence. Scheme facts must come from retrieved
    evidence.
"""
            ),
            (
                "human",
                """
CONVERSATION HISTORY:

{chat_history}


USER'S CURRENT QUESTION:

{question}


STANDALONE RETRIEVAL QUESTION:

{standalone_question}


ORIGINAL GOVERNMENT SOURCE EVIDENCE:

{vector_context}


KNOWLEDGE GRAPH INFORMATION:

{graph_context}


Using only the supplied evidence, answer the
user's current question.
"""
            )
        ]
    )
)


# ============================================================
# 8. CREATE LANGCHAIN CHAINS
# ============================================================

question_rewriter_chain = (
    question_rewriter_prompt
    | llm
)

answer_chain = (
    answer_prompt
    | llm
)


# ============================================================
# 9. FORMAT CHAT HISTORY
# ============================================================

def format_chat_history(
    chat_history,
    max_messages=6
):
    """
    Convert Streamlit conversation messages into
    text that the LLM can understand.

    We use only the most recent messages so the
    prompt does not grow forever.
    """

    if not chat_history:

        return "No previous conversation."

    recent_messages = chat_history[
        -max_messages:
    ]

    formatted_messages = []

    for message in recent_messages:

        role = message.get(
            "role",
            "user"
        )

        content = message.get(
            "content",
            ""
        )

        if role == "user":

            speaker = "User"

        else:

            speaker = "Assistant"

        formatted_messages.append(
            f"{speaker}: {content}"
        )

    return "\n\n".join(
        formatted_messages
    )


# ============================================================
# 10. CREATE STANDALONE QUESTION
# ============================================================

def create_standalone_question(
    question,
    chat_history
):
    """
    Rewrite a follow-up question into a standalone
    retrieval question.

    Example:

    History:
    User: Tell me about Kalaignarin Kanavu Illam.

    Current:
    What documents are needed?

    Result:
    What documents are needed for Kalaignarin
    Kanavu Illam?
    """

    if not chat_history:

        return question

    formatted_history = (
        format_chat_history(
            chat_history
        )
    )

    response = (
        question_rewriter_chain.invoke(
            {
                "chat_history":
                    formatted_history,

                "question":
                    question,
            }
        )
    )

    standalone_question = (
        response.content.strip()
    )

    if not standalone_question:

        return question

    return standalone_question


# ============================================================
# 11. FORMAT VECTOR CONTEXT
# ============================================================

def format_vector_context(
    vector_results
):

    if not vector_results:

        return (
            "No relevant source chunks were retrieved."
        )

    sections = []

    for index, result in enumerate(
        vector_results,
        start=1
    ):

        section = f"""
SOURCE CHUNK {index}

Scheme:
{result.get("scheme_name", "")}

Similarity Score:
{result.get("score", 0):.4f}

Chunk Index:
{result.get("chunk_index", "")}

Government Source Text:
{result.get("chunk_text", "")}

Source URL:
{result.get("source_url", "")}
"""

        sections.append(
            section.strip()
        )

    return "\n\n".join(
        sections
    )


# ============================================================
# 12. FORMAT GRAPH LIST
# ============================================================

def format_list(
    title,
    items
):

    if not items:

        return (
            f"{title}: None found"
        )

    formatted_items = "\n".join(
        f"- {item}"
        for item in items
    )

    return (
        f"{title}:\n"
        f"{formatted_items}"
    )


# ============================================================
# 13. FORMAT GRAPH CONTEXT
# ============================================================

def format_graph_context(
    graph_results
):

    if not graph_results:

        return (
            "No related knowledge graph "
            "information was retrieved."
        )

    sections = []

    for scheme_name, data in (
        graph_results.items()
    ):

        section_parts = [

            f"SCHEME: {scheme_name}",

            (
                f"Description: "
                f"{data.get('description', '')}"
            ),

            (
                f"Scheme Type: "
                f"{data.get('scheme_type', '')}"
            ),

            format_list(
                "Departments",
                data.get(
                    "departments",
                    []
                )
            ),

            format_list(
                "Beneficiaries",
                data.get(
                    "beneficiaries",
                    []
                )
            ),

            format_list(
                "Eligibility",
                data.get(
                    "eligibility",
                    []
                )
            ),

            format_list(
                "Benefits",
                data.get(
                    "benefits",
                    []
                )
            ),

            format_list(
                "Required Documents",
                data.get(
                    "documents",
                    []
                )
            ),

            format_list(
                "Locations",
                data.get(
                    "locations",
                    []
                )
            ),

            format_list(
                "Activities",
                data.get(
                    "activities",
                    []
                )
            ),

            (
                f"Source URL: "
                f"{data.get('source_url', '')}"
            ),
        ]

        sections.append(
            "\n".join(
                section_parts
            )
        )

    return "\n\n".join(
        sections
    )


# ============================================================
# 14. GENERATE GROUNDED ANSWER
# ============================================================

def generate_answer(
    question,
    chat_history=None,
    top_k=3
):
    """
    Complete conversational GraphRAG pipeline.

    Chat History
        +
    Current Question
        ↓
    Question Rewriter
        ↓
    Standalone Question
        ↓
    Hybrid Retrieval
        ↓
    Vector + Graph Context
        ↓
    Answer Generator
        ↓
    Grounded Response
    """

    if chat_history is None:

        chat_history = []

    # --------------------------------------------------------
    # A. Rewrite follow-up into standalone query
    # --------------------------------------------------------

    standalone_question = (
        create_standalone_question(
            question=question,
            chat_history=chat_history
        )
    )

    # --------------------------------------------------------
    # B. Retrieve using standalone question
    # --------------------------------------------------------

    retrieval_results = (
        hybrid_retrieve(
            question=standalone_question,
            top_k=top_k
        )
    )

    # --------------------------------------------------------
    # C. Format vector evidence
    # --------------------------------------------------------

    vector_context = (
        format_vector_context(
            retrieval_results[
                "vector_results"
            ]
        )
    )

    # --------------------------------------------------------
    # D. Format graph evidence
    # --------------------------------------------------------

    graph_context = (
        format_graph_context(
            retrieval_results[
                "graph_results"
            ]
        )
    )

    # --------------------------------------------------------
    # E. Format conversation
    # --------------------------------------------------------

    formatted_history = (
        format_chat_history(
            chat_history
        )
    )

    # --------------------------------------------------------
    # F. Generate final answer
    # --------------------------------------------------------

    response = (
        answer_chain.invoke(
            {
                "chat_history":
                    formatted_history,

                "question":
                    question,

                "standalone_question":
                    standalone_question,

                "vector_context":
                    vector_context,

                "graph_context":
                    graph_context,
            }
        )
    )

    # --------------------------------------------------------
    # G. Return answer + debug information
    # --------------------------------------------------------

    return {

        "answer":
            response.content,

        "standalone_question":
            standalone_question,

        "retrieval":
            retrieval_results,

        "vector_context":
            vector_context,

        "graph_context":
            graph_context,
    }


# ============================================================
# 15. MAIN TERMINAL TEST
# ============================================================

def main():

    conversation = []

    try:

        driver.verify_connectivity()

        print(
            "✓ Connected to Neo4j"
        )

        print()
        print(
            "======================================"
        )
        print(
            "CONVERSATIONAL TN SCHEME GRAPHRAG"
        )
        print(
            "======================================"
        )

        print()
        print(
            "Type 'exit' to stop."
        )

        # ----------------------------------------------------
        # Continuous conversation loop
        # ----------------------------------------------------

        while True:

            print()

            question = input(
                "You: "
            ).strip()

            if not question:

                continue

            if question.lower() in {
                "exit",
                "quit"
            }:

                break

            # ------------------------------------------------
            # Generate answer using previous conversation
            # ------------------------------------------------

            result = generate_answer(
                question=question,
                chat_history=conversation,
                top_k=3
            )

            print()
            print(
                "Standalone retrieval question:"
            )

            print(
                result[
                    "standalone_question"
                ]
            )

            print()
            print(
                "Assistant:"
            )

            print(
                result[
                    "answer"
                ]
            )

            # ------------------------------------------------
            # Save conversation AFTER generation
            # ------------------------------------------------

            conversation.append(
                {
                    "role": "user",
                    "content": question
                }
            )

            conversation.append(
                {
                    "role": "assistant",
                    "content": result[
                        "answer"
                    ]
                }
            )

    finally:

        driver.close()

        print()
        print(
            "Neo4j connection closed."
        )


# ============================================================
# 16. RUN TERMINAL TEST
# ============================================================

if __name__ == "__main__":
    main()