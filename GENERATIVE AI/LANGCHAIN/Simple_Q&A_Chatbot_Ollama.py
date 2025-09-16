import streamlit as st
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_core.output_parsers import StrOutputParser

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# LangSmith tracking (optional)
os.environ['LANGCHAIN_API_KEY'] = os.getenv('LANGCHAIN_API_KEY')
os.environ['LANGSMITH_TRACING_V2'] = "true"
os.environ['LANGCHAIN_PROJECT'] = "Q&A Chatbot with Ollama"

# --- Streamlit UI ---
st.set_page_config(page_title="ChatOllama Q&A", page_icon="🦙")
st.title("🦙 Q&A Chatbot with ChatOllama")

# Sidebar settings
st.sidebar.header("⚙️ Model Settings")

# Dropdown for model selection
model_choice = st.sidebar.selectbox(
    "Choose a model:",
    ["llama3.1", "mistral", "gemma", "codellama", "phi3"]
)

temperature = st.sidebar.slider("Temperature", 0.0, 1.0, 0.7, 0.1)
max_tokens = st.sidebar.slider("Max Tokens (num_predict)", 50, 2048, 512, 50)

# --- Prompt ---
prompt = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(
        "You are a helpful assistant. Please answer clearly and concisely."
    ),
    HumanMessagePromptTemplate.from_template("Question: {question}")
])

# --- LLM ---
llm = ChatOllama(
    model=model_choice,
    temperature=temperature,
    num_predict=max_tokens
)

# Parser
parser = StrOutputParser()

# Chain
chain = prompt | llm | parser

# --- User Input ---
user_question = st.text_input("💬 Ask me anything:")

if st.button("🚀 Get Answer"):
    if user_question.strip():
        with st.spinner(f"Thinking with {model_choice}... 🤔"):
            try:
                response = chain.invoke({"question": user_question})
                st.success(response)
            except Exception as e:
                st.error(f"⚠️ Error: {e}")
    else:
        st.warning("Please enter a question first.")
