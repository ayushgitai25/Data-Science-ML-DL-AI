import os
import streamlit as st
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
os.environ['LANGCHAIN_API_KEY'] = os.getenv('LANGCHAIN_API_KEY')  # for LangSmith Tracking
os.environ['LANGSMITH_TRACING_V2'] = "true"
os.environ['LANGCHAIN_PROJECT'] = os.getenv('LANGCHAIN_PROJECT')

# LangChain imports
from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate
from langchain.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_ollama import OllamaLLM
from langchain_core.output_parsers import StrOutputParser

# ---------------------------
# Streamlit UI
# ---------------------------
st.set_page_config(page_title="LangChain RAG with Ollama", page_icon="🦙", layout="centered")

st.title("🦙 LangChain RAG App with Ollama")
st.markdown("Ask questions about the LangChain docs (retrieved from web).")

# Load documents (cached so it doesn't reload every time)
@st.cache_resource
def load_docs():
    loader = WebBaseLoader("https://python.langchain.com/docs/introduction/")
    docs = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    return text_splitter.split_documents(docs)

splitted_docs = load_docs()

# LLM and Chain setup
llm = OllamaLLM(model="llama3.1")

prompt = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template("You are a helpful assistant. Please respond to the question asked."),
    HumanMessagePromptTemplate.from_template("Question: {question}")
])

output_parser = StrOutputParser()
chain = prompt | llm | output_parser

# User input
question = st.text_input("💬 Enter your question:")

if st.button("Ask"):
    if question.strip():
        with st.spinner("Thinking..."):
            response = chain.invoke({"question": question})
        st.success("✅ Answer:")
        st.write(response)
    else:
        st.warning("⚠️ Please enter a question.")
