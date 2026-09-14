# ============================================================
# 1. IMPORTS
# ============================================================

import os
import streamlit as st
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory


# ============================================================
# 2. LOAD ENVIRONMENT VARIABLES FROM .env
# ============================================================

# Load variables from the .env file
load_dotenv()

# Read the OpenAI API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Check whether the key exists
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
    page_title="AI Chef Assistant",
    page_icon="🍳",
    layout="centered"
)

st.title("🍳 Your AI Chef Assistant")

st.caption(
    "Ask for recipes, cooking tips, or modification ideas "
    "based on your conversation history!"
)


# ============================================================
# 4. INITIALIZE LANGCHAIN COMPONENTS
# ============================================================

@st.cache_resource
def init_langchain():

    # --------------------------------------------------------
    # Initialize OpenAI Model
    # --------------------------------------------------------

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.7
    )

    # --------------------------------------------------------
    # Create Prompt Template
    # --------------------------------------------------------

    prompt_template = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
                You are an expert chef.

                Help the user with:
                - Recipes
                - Cooking advice
                - Ingredient substitutions
                - Meal ideas
                - Recipe modifications
                - Cooking techniques

                Use the conversation history when relevant.
                """
            ),

            # Previous conversation goes here
            MessagesPlaceholder(
                variable_name="chat_history"
            ),

            # Current user input
            (
                "user",
                "{input}"
            )
        ]
    )

    # --------------------------------------------------------
    # Create LangChain Pipeline
    # --------------------------------------------------------

    base_chain = (
        prompt_template
        | llm
        | StrOutputParser()
    )

    return base_chain


# Initialize chain
base_chain = init_langchain()


# ============================================================
# 5. INITIALIZE CHAT MEMORY
# ============================================================

if "chat_history" not in st.session_state:

    st.session_state.chat_history = (
        InMemoryChatMessageHistory()
    )


# ============================================================
# 6. GET SESSION HISTORY
# ============================================================

def get_session_history(session_id: str):

    return st.session_state.chat_history


# ============================================================
# 7. ADD MEMORY TO LANGCHAIN
# ============================================================

conversational_chain = RunnableWithMessageHistory(

    base_chain,

    get_session_history,

    input_messages_key="input",

    history_messages_key="chat_history"
)


# ============================================================
# 8. DISPLAY EXISTING CHAT HISTORY
# ============================================================

for message in st.session_state.chat_history.messages:

    if message.type == "human":
        role = "user"
    else:
        role = "assistant"

    with st.chat_message(role):
        st.markdown(message.content)


# ============================================================
# 9. GET USER INPUT
# ============================================================

user_input = st.chat_input(
    "What ingredients do you have?"
)


# ============================================================
# 10. PROCESS USER INPUT
# ============================================================

if user_input:

    # --------------------------------------------------------
    # Display User Message
    # --------------------------------------------------------

    with st.chat_message("user"):
        st.markdown(user_input)

    # --------------------------------------------------------
    # Configure Session
    # --------------------------------------------------------

    config = {
        "configurable": {
            "session_id": "streamlit_session"
        }
    }

    # --------------------------------------------------------
    # Generate AI Response
    # --------------------------------------------------------

    with st.chat_message("assistant"):

        response = st.write_stream(
            conversational_chain.stream(
                {
                    "input": user_input
                },
                config=config
            )
        )