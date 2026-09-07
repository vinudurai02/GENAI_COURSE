
import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
#os.environ["OPENAI_API_KEY"] = "YOUR_OPENAI_API_KEY"


# ============================================================
# 1. IMPORTS
# ============================================================

from langchain_openai import ChatOpenAI
from langchain_community.tools import DuckDuckGoSearchRun
from langchain.agents import create_agent


# ============================================================
# 2. INITIALIZE MODEL
# ============================================================

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0
)


# ============================================================
# 3. CREATE TOOLS
# ============================================================

search_tool = DuckDuckGoSearchRun()

tools = [search_tool]


# ============================================================
# 4. CREATE AGENT
# ============================================================

agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt=(
        "You are a helpful assistant. "
        "Use the search tool when current information is needed."
    )
)


# ============================================================
# 5. CHAT LOOP
# ============================================================

print("\nAI Agent Started")
print("Type 'exit' to stop.\n")

while True:

    query = input("You: ")

    # --------------------------------------------------------
    # Exit condition
    # --------------------------------------------------------

    if query.lower() in ["exit", "quit"]:
        print("\nGoodbye!")
        break

    # --------------------------------------------------------
    # Send question to agent
    # --------------------------------------------------------

    response = agent.invoke({
        "messages": [
            {
                "role": "user",
                "content": query
            }
        ]
    })

    # --------------------------------------------------------
    # Extract final answer
    # --------------------------------------------------------

    final_message = response["messages"][-1]

    print("\nAgent:", final_message.content)
    print()