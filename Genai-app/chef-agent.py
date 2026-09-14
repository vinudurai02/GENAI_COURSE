# ============================================================
# AI DOCUMENT CHAT ASSISTANT
# RAG + CONVERSATIONAL MEMORY + STREAMLIT
# ============================================================


# ============================================================
# 1. IMPORTS
# ============================================================

import os
import tempfile

import streamlit as st
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI

from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
)

from langchain_core.messages import (
    HumanMessage,
    AIMessage,
)

from langchain_core.output_parsers import StrOutputParser

from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS

from langchain_huggingface import HuggingFaceEmbeddings

from langchain_text_splitters import RecursiveCharacterTextSplitter


# ============================================================
# 2. LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


# Check whether OpenAI API key exists
if not OPENAI_API_KEY:

    st.error(
        "OPENAI_API_KEY is missing. "
        "Please add it to your .env file."
    )

    st.stop()


# ============================================================
# 3. STREAMLIT PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="AI Document Chat Assistant",
    page_icon="📚",
    layout="wide",
)


st.title("📚 AI Document Chat Assistant")

st.caption(
    "Upload PDF documents and ask questions using "
    "RAG + Conversational Memory."
)


# ============================================================
# 4. INITIALIZE SESSION STATE
# ============================================================

# Store conversation history

if "messages" not in st.session_state:

    st.session_state.messages = []


# Store FAISS vector database

if "vectorstore" not in st.session_state:

    st.session_state.vectorstore = None


# Store retriever

if "retriever" not in st.session_state:

    st.session_state.retriever = None


# Keep track of processed files

if "processed_files" not in st.session_state:

    st.session_state.processed_files = []


# ============================================================
# 5. INITIALIZE OPENAI MODEL
# ============================================================

@st.cache_resource
def load_llm():

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.2,
    )

    return llm


llm = load_llm()


# ============================================================
# 6. INITIALIZE HUGGINGFACE EMBEDDINGS
# ============================================================

@st.cache_resource
def load_embeddings():

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    return embeddings


embeddings = load_embeddings()


# ============================================================
# 7. TEXT SPLITTER
# ============================================================

text_splitter = RecursiveCharacterTextSplitter(

    chunk_size=1000,

    chunk_overlap=200,

    length_function=len,
)


# ============================================================
# 8. PDF PROCESSING FUNCTION
# ============================================================

def process_pdfs(uploaded_files):

    all_documents = []

    # --------------------------------------------------------
    # Loop through every uploaded PDF
    # --------------------------------------------------------

    for uploaded_file in uploaded_files:

        # Create temporary PDF file
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".pdf",
        ) as temp_file:

            temp_file.write(uploaded_file.getbuffer())

            temp_file_path = temp_file.name

        try:

            # ------------------------------------------------
            # Load PDF
            # ------------------------------------------------

            loader = PyPDFLoader(temp_file_path)

            documents = loader.load()


            # ------------------------------------------------
            # Add filename metadata
            # ------------------------------------------------

            for document in documents:

                document.metadata["source_file"] = (
                    uploaded_file.name
                )


            all_documents.extend(documents)

        finally:

            # Delete temporary file
            os.remove(temp_file_path)


    # --------------------------------------------------------
    # Split documents into smaller chunks
    # --------------------------------------------------------

    chunks = text_splitter.split_documents(
        all_documents
    )


    # --------------------------------------------------------
    # Create FAISS vector database
    # --------------------------------------------------------

    vectorstore = FAISS.from_documents(
        chunks,
        embeddings,
    )


    return vectorstore, chunks


# ============================================================
# 9. FORMAT RETRIEVED DOCUMENTS
# ============================================================

def format_documents(documents):

    formatted_context = []


    for index, document in enumerate(
        documents,
        start=1,
    ):

        source = document.metadata.get(
            "source_file",
            "Unknown"
        )

        page = document.metadata.get(
            "page",
            "Unknown"
        )


        formatted_text = f"""
Document {index}

Source: {source}
Page: {page}

Content:
{document.page_content}
"""

        formatted_context.append(
            formatted_text
        )


    return "\n\n".join(formatted_context)


# ============================================================
# 10. CREATE RAG PROMPT
# ============================================================

rag_prompt = ChatPromptTemplate.from_messages(

    [

        # ----------------------------------------------------
        # System instructions
        # ----------------------------------------------------

        (
            "system",
            """
You are an intelligent document assistant.

Your job is to answer questions using the supplied
document context.

Rules:

1. Use the provided document context whenever possible.

2. Use the conversation history to understand follow-up
   questions.

3. Do not invent information that is not supported by
   the documents.

4. If the answer cannot be found in the documents,
   clearly say:

   "I couldn't find that information in the uploaded documents."

5. When useful, mention the source document and page.

6. Explain technical topics clearly and step by step.

7. If the user asks a follow-up question such as
   "why?", "what about that?", "compare them", or
   "explain this", use the conversation history to
   understand what they are referring to.

DOCUMENT CONTEXT:

{context}
"""
        ),


        # ----------------------------------------------------
        # Previous conversation
        # ----------------------------------------------------

        MessagesPlaceholder(
            variable_name="chat_history"
        ),


        # ----------------------------------------------------
        # Current user question
        # ----------------------------------------------------

        (
            "user",
            "{question}"
        ),
    ]
)


# ============================================================
# 11. CREATE LANGCHAIN LCEL CHAIN
# ============================================================

rag_chain = (

    rag_prompt

    | llm

    | StrOutputParser()

)


# ============================================================
# 12. SIDEBAR
# ============================================================

with st.sidebar:

    st.header("📄 Documents")


    # --------------------------------------------------------
    # PDF Upload
    # --------------------------------------------------------

    uploaded_files = st.file_uploader(

        "Upload PDF documents",

        type=["pdf"],

        accept_multiple_files=True,
    )


    # --------------------------------------------------------
    # Process Documents Button
    # --------------------------------------------------------

    if st.button(
        "Process Documents",
        use_container_width=True,
    ):

        if not uploaded_files:

            st.warning(
                "Please upload at least one PDF."
            )

        else:

            with st.spinner(
                "Processing documents..."
            ):

                try:

                    vectorstore, chunks = process_pdfs(
                        uploaded_files
                    )


                    # Store vector database
                    st.session_state.vectorstore = (
                        vectorstore
                    )


                    # Create retriever
                    st.session_state.retriever = (
                        vectorstore.as_retriever(
                            search_kwargs={
                                "k": 4
                            }
                        )
                    )


                    # Store filenames
                    st.session_state.processed_files = [

                        file.name

                        for file in uploaded_files
                    ]


                    st.success(
                        f"Processed "
                        f"{len(uploaded_files)} document(s)"
                    )


                    st.info(
                        f"Created {len(chunks)} text chunks."
                    )


                except Exception as error:

                    st.error(
                        f"Error processing documents: "
                        f"{error}"
                    )


    # --------------------------------------------------------
    # Show Processed Files
    # --------------------------------------------------------

    if st.session_state.processed_files:

        st.divider()

        st.subheader(
            "Processed Documents"
        )


        for filename in (
            st.session_state.processed_files
        ):

            st.write(
                f"✅ {filename}"
            )


    # --------------------------------------------------------
    # Clear Conversation
    # --------------------------------------------------------

    st.divider()


    if st.button(
        "🗑️ Clear Chat",
        use_container_width=True,
    ):

        st.session_state.messages = []

        st.rerun()


# ============================================================
# 13. DISPLAY CHAT HISTORY
# ============================================================

for message in st.session_state.messages:

    with st.chat_message(
        message["role"]
    ):

        st.markdown(
            message["content"]
        )


# ============================================================
# 14. GET USER QUESTION
# ============================================================

user_question = st.chat_input(

    "Ask a question about your documents..."

)


# ============================================================
# 15. PROCESS USER QUESTION
# ============================================================

if user_question:


    # --------------------------------------------------------
    # Check whether documents have been processed
    # --------------------------------------------------------

    if st.session_state.retriever is None:

        st.warning(
            "Please upload and process at least "
            "one PDF first."
        )

        st.stop()


    # --------------------------------------------------------
    # Display user question
    # --------------------------------------------------------

    with st.chat_message("user"):

        st.markdown(
            user_question
        )


    # --------------------------------------------------------
    # Save user message
    # --------------------------------------------------------

    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_question,
        }
    )


    # ========================================================
    # 16. RETRIEVE RELEVANT DOCUMENT CHUNKS
    # ========================================================

    retrieved_documents = (

        st.session_state.retriever.invoke(
            user_question
        )

    )


    # ========================================================
    # 17. FORMAT RETRIEVED CONTEXT
    # ========================================================

    context = format_documents(
        retrieved_documents
    )


    # ========================================================
    # 18. CONVERT STREAMLIT HISTORY TO LANGCHAIN HISTORY
    # ========================================================

    chat_history = []


    # Do not include latest question because it is already
    # passed separately as {question}

    previous_messages = (
        st.session_state.messages[:-1]
    )


    for message in previous_messages:

        if message["role"] == "user":

            chat_history.append(

                HumanMessage(
                    content=message["content"]
                )

            )

        elif message["role"] == "assistant":

            chat_history.append(

                AIMessage(
                    content=message["content"]
                )

            )


    # ========================================================
    # 19. GENERATE ANSWER
    # ========================================================

    with st.chat_message(
        "assistant"
    ):

        try:

            response = st.write_stream(

                rag_chain.stream(

                    {

                        "context": context,

                        "chat_history": (
                            chat_history
                        ),

                        "question": (
                            user_question
                        ),

                    }

                )

            )


        except Exception as error:

            st.error(
                f"Error generating response: "
                f"{error}"
            )

            st.stop()


    # ========================================================
    # 20. SAVE AI RESPONSE TO MEMORY
    # ========================================================

    st.session_state.messages.append(

        {

            "role": "assistant",

            "content": response,

        }

    )


    # ========================================================
    # 21. SHOW RETRIEVED SOURCES
    # ========================================================

    with st.expander(
        "🔍 View Retrieved Context"
    ):

        for index, document in enumerate(

            retrieved_documents,

            start=1,

        ):

            source = document.metadata.get(
                "source_file",
                "Unknown"
            )

            page = document.metadata.get(
                "page",
                "Unknown"
            )


            st.markdown(
                f"### Result {index}"
            )


            st.write(
                f"**Source:** {source}"
            )


            if isinstance(page, int):

                st.write(
                    f"**Page:** {page + 1}"
                )

            else:

                st.write(
                    f"**Page:** {page}"
                )


            st.write(
                document.page_content
            )


            st.divider()