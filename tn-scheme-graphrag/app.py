# ============================================================
# 1. IMPORTS
# ============================================================

import sys
from pathlib import Path

import streamlit as st


# ============================================================
# 2. PROJECT PATH SETUP
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent

SRC_PATH = (
    PROJECT_ROOT
    / "src"
)

if str(SRC_PATH) not in sys.path:

    sys.path.insert(
        0,
        str(SRC_PATH)
    )


# ============================================================
# 3. IMPORT GRAPHRAG
# ============================================================

from rag import generate_answer


# ============================================================
# 4. STREAMLIT PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Tamil Nadu Scheme Assistant",
    page_icon="🏛️",
    layout="centered",
    initial_sidebar_state="expanded"
)


# ============================================================
# 5. APPLICATION HEADER
# ============================================================

st.title(
    "🏛️ Tamil Nadu Scheme Assistant"
)

st.caption(
    "Conversational GraphRAG assistant for "
    "Tamil Nadu Government schemes."
)


# ============================================================
# 6. INITIALIZE SESSION STATE
# ============================================================

if "messages" not in st.session_state:

    st.session_state.messages = []


# ============================================================
# 7. SIDEBAR
# ============================================================

with st.sidebar:

    st.header(
        "About"
    )

    st.write(
        """
        This assistant combines:

        • Semantic vector search

        • Neo4j knowledge graph

        • Conversational context

        • OpenAI generation
        """
    )

    st.divider()

    st.subheader(
        "Try a conversation"
    )

    st.write(
        """
        **You:** Tell me about Kalaignarin
        Kanavu Illam.

        **Then ask:** What documents are needed?

        **Then ask:** How much funding is provided?
        """
    )

    st.divider()

    if st.button(
        "🗑️ Clear conversation",
        use_container_width=True
    ):

        st.session_state.messages = []

        st.rerun()


# ============================================================
# 8. DISPLAY PREVIOUS CONVERSATION
# ============================================================

for message in st.session_state.messages:

    with st.chat_message(
        message["role"]
    ):

        st.markdown(
            message["content"]
        )


# ============================================================
# 9. CHAT INPUT
# ============================================================

user_question = st.chat_input(
    "Ask about a Tamil Nadu Government scheme..."
)


# ============================================================
# 10. PROCESS QUESTION
# ============================================================

if user_question:

    # --------------------------------------------------------
    # IMPORTANT:
    # Capture OLD history before adding current question.
    # --------------------------------------------------------

    previous_history = (
        st.session_state.messages.copy()
    )

    # --------------------------------------------------------
    # Display current user message
    # --------------------------------------------------------

    with st.chat_message(
        "user"
    ):

        st.markdown(
            user_question
        )

    # --------------------------------------------------------
    # Add current user message to UI history
    # --------------------------------------------------------

    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_question
        }
    )

    # --------------------------------------------------------
    # Generate conversational GraphRAG answer
    # --------------------------------------------------------

    with st.chat_message(
        "assistant"
    ):

        with st.spinner(
            "Searching Tamil Nadu Government schemes..."
        ):

            try:

                result = generate_answer(
                    question=user_question,

                    # ----------------------------------------
                    # Only PREVIOUS conversation goes here.
                    # ----------------------------------------

                    chat_history=previous_history,

                    top_k=3
                )

                answer = result[
                    "answer"
                ]

                standalone_question = result[
                    "standalone_question"
                ]

                retrieval = result[
                    "retrieval"
                ]

                # ------------------------------------------------
                # Display answer
                # ------------------------------------------------

                st.markdown(
                    answer
                )

                # ------------------------------------------------
                # Development / learning information
                # ------------------------------------------------

                with st.expander(
                    "🧠 View GraphRAG reasoning pipeline"
                ):

                    st.markdown(
                        "### Current question"
                    )

                    st.write(
                        user_question
                    )

                    st.markdown(
                        "### Standalone retrieval question"
                    )

                    st.info(
                        standalone_question
                    )

                    st.markdown(
                        "### Retrieved schemes"
                    )

                    scheme_names = (
                        retrieval.get(
                            "scheme_names",
                            []
                        )
                    )

                    if scheme_names:

                        for scheme_name in (
                            scheme_names
                        ):

                            st.write(
                                f"• {scheme_name}"
                            )

                    else:

                        st.write(
                            "No schemes retrieved."
                        )

                    # --------------------------------------------
                    # Vector search results
                    # --------------------------------------------

                    st.markdown(
                        "### Vector search"
                    )

                    vector_results = (
                        retrieval.get(
                            "vector_results",
                            []
                        )
                    )

                    for index, item in enumerate(
                        vector_results,
                        start=1
                    ):

                        st.markdown(
                            f"**Result {index}**"
                        )

                        st.write(
                            "Scheme:",
                            item[
                                "scheme_name"
                            ]
                        )

                        st.write(
                            "Similarity:",
                            f"{item['score']:.4f}"
                        )

                        st.write(
                            "Chunk:",
                            item[
                                "chunk_index"
                            ]
                        )

                        st.caption(
                            item[
                                "chunk_text"
                            ][:400]
                        )

                        st.divider()

                # ------------------------------------------------
                # Save assistant response
                # ------------------------------------------------

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": answer
                    }
                )

            except Exception as error:

                st.error(
                    "Something went wrong while "
                    "processing your question."
                )

                with st.expander(
                    "Technical details"
                ):

                    st.code(
                        str(error)
                    )