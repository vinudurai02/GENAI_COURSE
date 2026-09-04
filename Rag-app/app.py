# ============================================================
# 1. IMPORT REQUIRED LIBRARIES
# ============================================================

import os

import streamlit as st
from pypdf import PdfReader

from dotenv import load_dotenv

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI

load_dotenv()


# ============================================================
# 2. BUILD STREAMLIT USER INTERFACE
# ============================================================

st.title("PDF RAG App")

st.write(
    "Upload a PDF and ask questions about its contents."
)


# ============================================================
# 3. INITIALIZE STREAMLIT SESSION STATE
# ============================================================
#
# Streamlit reruns app.py whenever the user interacts
# with the application.
#
# Session state keeps the FAISS vector database alive
# during the current browser session.
# ============================================================

if "vector_store" not in st.session_state:
    st.session_state.vector_store = None

if "processed_file" not in st.session_state:
    st.session_state.processed_file = None

if "chunk_count" not in st.session_state:
    st.session_state.chunk_count = 0


# ============================================================
# 4. LOAD THE HUGGING FACE EMBEDDING MODEL
# ============================================================
#
# @st.cache_resource tells Streamlit:
#
# "Load this expensive model once and reuse it."
#
# Without this, the embedding model itself could be loaded
# repeatedly during Streamlit reruns.
# ============================================================

@st.cache_resource
def load_embedding_model():

    embeddings = HuggingFaceEmbeddings(
        model_name=(
            "sentence-transformers/"
            "all-MiniLM-L6-v2"
        )
    )

    return embeddings


# ============================================================
# 5. LOAD THE OPENAI LANGUAGE MODEL
# ============================================================
#
# The API key is NOT written inside the code.
#
# ChatOpenAI automatically reads:
#
# OPENAI_API_KEY
#
# from the environment.
# ============================================================

@st.cache_resource
def load_llm():

    llm = ChatOpenAI(
        model="gpt-4.1-mini",
        temperature=0
    )

    return llm


# ============================================================
# 6. PDF FILE UPLOADER
# ============================================================

uploaded_file = st.file_uploader(
    "Upload a PDF",
    type="pdf"
)


# ============================================================
# 7. CHECK WHETHER A NEW PDF NEEDS TO BE PROCESSED
# ============================================================
#
# We use the file name + size as a simple file identifier.
#
# If the uploaded file changes, we rebuild the database.
#
# If the file has already been processed, we reuse
# the existing vector database.
# ============================================================

if uploaded_file is not None:

    file_id = f"{uploaded_file.name}-{uploaded_file.size}"

    if st.session_state.processed_file != file_id:

        # Clear previous vector database.

        st.session_state.vector_store = None
        st.session_state.chunk_count = 0


        # ====================================================
        # 8. EXTRACT TEXT FROM THE PDF
        # ====================================================

        with st.spinner("Reading PDF..."):

            reader = PdfReader(uploaded_file)

            documents = []

            for page_number, page in enumerate(reader.pages):

                page_text = page.extract_text()

                if page_text and page_text.strip():

                    document = Document(
                        page_content=page_text,
                        metadata={
                            "page": page_number + 1,
                            "source": uploaded_file.name
                        }
                    )

                    documents.append(document)


        # ====================================================
        # 9. CHECK FOR UNREADABLE / SCANNED PDF
        # ====================================================

        if not documents:

            st.error(
                "No readable text was found in this PDF."
            )

        else:

            st.success(
                f"PDF text extracted successfully from "
                f"{len(documents)} pages."
            )


            # =================================================
            # 10. SPLIT PDF INTO SMALLER CHUNKS
            # =================================================
            #
            # chunk_size:
            # Maximum approximate size of each chunk.
            #
            # chunk_overlap:
            # Repeats some text between neighboring chunks
            # so context is not lost at chunk boundaries.
            # =================================================

            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=700,
                chunk_overlap=120
            )

            chunks = text_splitter.split_documents(
                documents
            )

            st.session_state.chunk_count = len(chunks)


            # =================================================
            # 11. CREATE EMBEDDINGS
            # =================================================
            #
            # Each chunk is converted into a numerical vector
            # representing its semantic meaning.
            # =================================================

            embeddings = load_embedding_model()


            # =================================================
            # 12. BUILD THE FAISS VECTOR DATABASE
            # =================================================
            #
            # FAISS stores the chunk vectors and allows us
            # to search for semantically similar chunks.
            # =================================================

            with st.spinner(
                "Creating embeddings and building "
                "vector database..."
            ):

                vector_store = FAISS.from_documents(
                    chunks,
                    embeddings
                )

                st.session_state.vector_store = vector_store

                st.session_state.processed_file = file_id


            st.success(
                "Vector database is ready!"
            )


# ============================================================
# 13. DISPLAY VECTOR DATABASE STATUS
# ============================================================

if st.session_state.vector_store is not None:

    st.success(
        f"Vector database ready — "
        f"{st.session_state.chunk_count} chunks indexed."
    )


    # ========================================================
    # 14. CREATE QUESTION FORM
    # ========================================================
    #
    # A form is useful because the query is only processed
    # when the user presses the Ask button.
    # ========================================================

    with st.form("question_form"):

        query = st.text_input(
            "Ask a question about your PDF"
        )

        submitted = st.form_submit_button(
            "Ask"
        )


    # ========================================================
    # 15. PROCESS THE USER QUESTION
    # ========================================================

    if submitted and query.strip():


        # ====================================================
        # 16. CREATE A LANGCHAIN RETRIEVER
        # ====================================================
        #
        # Instead of calling FAISS similarity_search directly,
        # we expose FAISS as a LangChain Retriever.
        #
        # k=5 means:
        #
        # Retrieve the five most relevant chunks.
        # ====================================================

        retriever = (
            st.session_state.vector_store.as_retriever(
                search_kwargs={
                    "k": 5
                }
            )
        )


        # ====================================================
        # 17. RETRIEVE RELEVANT PDF CHUNKS
        # ====================================================

        with st.spinner(
            "Searching the PDF..."
        ):

            retrieved_docs = retriever.invoke(
                query
            )


        # ====================================================
        # 18. COMBINE RETRIEVED CHUNKS INTO CONTEXT
        # ====================================================
        #
        # The LLM does NOT read the entire PDF.
        #
        # It receives only the chunks found by retrieval.
        #
        # These retrieved chunks become the "context"
        # part of Retrieval-Augmented Generation.
        # ====================================================

        context_parts = []

        for doc in retrieved_docs:

            page_number = doc.metadata.get(
                "page",
                "Unknown"
            )

            context_parts.append(
                f"Page {page_number}:\n"
                f"{doc.page_content}"
            )

        context = "\n\n".join(
            context_parts
        )


        # ====================================================
        # 19. CREATE THE RAG PROMPT
        # ====================================================
        #
        # The prompt contains:
        #
        # 1. Instructions
        # 2. Retrieved PDF context
        # 3. User question
        #
        # This is the "Augmented" part of RAG.
        # ====================================================

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """
You are a helpful assistant answering questions
about an uploaded PDF.

Answer the question using only the information
contained in the provided context.

Do not use outside knowledge.

If the answer cannot be found in the context,
say:

"I could not find this information in the uploaded PDF."

Keep the answer clear and concise.
"""
                ),
                (
                    "human",
                    """
Context:

{context}


Question:

{question}
"""
                )
            ]
        )


        # ====================================================
        # 20. LOAD THE OPENAI MODEL
        # ====================================================

        llm = load_llm()


        # ====================================================
        # 21. CREATE THE LANGCHAIN GENERATION CHAIN
        # ====================================================
        #
        # The | operator creates a simple LangChain pipeline:
        #
        # Prompt
        #   ↓
        # OpenAI model
        #
        # ====================================================

        chain = prompt | llm


        # ====================================================
        # 22. SEND CONTEXT + QUESTION TO OPENAI
        # ====================================================

        with st.spinner(
            "Generating answer..."
        ):

            response = chain.invoke(
                {
                    "context": context,
                    "question": query
                }
            )


        # ====================================================
        # 23. DISPLAY FINAL RAG ANSWER
        # ====================================================

        st.subheader(
            "Answer"
        )

        st.write(
            response.content
        )


        # ====================================================
        # 24. SHOW THE RETRIEVED SOURCE CHUNKS
        # ====================================================
        #
        # We keep this section visible for learning/debugging.
        #
        # It helps us understand WHY the model produced
        # a particular answer.
        # ====================================================

        with st.expander(
            "View retrieved chunks"
        ):

            for i, doc in enumerate(
                retrieved_docs,
                start=1
            ):

                page_number = doc.metadata.get(
                    "page",
                    "Unknown"
                )

                st.write(
                    f"### Chunk {i} — Page {page_number}"
                )

                st.write(
                    doc.page_content
                )


# ============================================================
# 25. WAITING STATE
# ============================================================

elif uploaded_file is None:

    st.info(
        "Upload a PDF to build the vector database."
    )