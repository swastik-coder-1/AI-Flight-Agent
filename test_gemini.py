import os
from langchain_google_genai import ChatGoogleGenerativeAI

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("ERROR: GEMINI_API_KEY is not set.")
    exit()

print("API key found!")

llm = ChatGoogleGenerativeAI(
    model="gemini-3.8-flash",
    temperature=0
)

response = llm.invoke("Say hello and tell me that you are working.")

print("\nGemini response:")
print(response.content)