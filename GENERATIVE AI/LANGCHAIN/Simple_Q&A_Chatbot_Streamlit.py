import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API keys
os.environ['GOOGLE_API_KEY'] = os.getenv('GOOGLE_API_KEY')
os.environ['LANGCHAIN_API_KEY'] = os.getenv('LANGCHAIN_API_KEY')  # For LangSmith Tracking
os.environ['LANGSMITH_TRACING_V2'] = "true"
os.environ['LANGCHAIN_PROJECT'] = "Simple Q&A Chatbot with Google Gemini"

# --- Streamlit App ---
st.set_page_config(page_title="LangChain Q&A Chatbot", page_icon="🤖")
st.title("🤖 Simple Q&A Chatbot with Google Gemini")

# Sidebar settings
st.sidebar.header("⚙️ Model Settings")
temperature = st.sidebar.slider("Temperature", 0.0, 1.0, 0.7, 0.1)
max_tokens = st.sidebar.slider("Max Tokens", 50, 2048, 512, 50)

# Build Prompt
prompt = ChatPromptTemplate.from_messages(
    [
        SystemMessagePromptTemplate.from_template(
            "You are a helpful assistant. Please answer the following question clearly and concisely."
        ),
        HumanMessagePromptTemplate.from_template("Question: {question}")
    ]
)

# LLM with adjustable params
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=temperature,
    max_output_tokens=max_tokens
)

# Parser
parser = StrOutputParser()

# Chain: Prompt → LLM → Parser
chain = prompt | llm | parser

# User input
user_question = st.text_input("💬 Ask me anything:")

if st.button("🚀 Get Answer"):
    if user_question.strip():
        with st.spinner("Thinking... 🤔"):
            try:
                response = chain.invoke({"question": user_question})
                st.success(response)
            except Exception as e:
                st.error(f"⚠️ Error: {e}")
    else:
        st.warning("Please enter a question first.")
