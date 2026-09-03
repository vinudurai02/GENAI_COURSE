from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

model = ChatOpenAI(model="gpt-4o-mini")

prompt = "Tell me a fun fact about Tamil Nadu."

response = model.invoke(prompt)

print("Input:", prompt)
print("Output:", response.content)
