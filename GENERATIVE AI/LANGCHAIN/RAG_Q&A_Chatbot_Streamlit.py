##=======================================================================

# 1. Data Ingestion : WebBaseLoader
# 2. Data Transformation : RecursiveCharacterTextSplitter
# 3. Embeddings and VectorDB
# 4. Create a reformulation_prompt=> SysMsg + MsgPlaceholder("chat_history")+HumanMsg("input")
# 5. Create history_aware_retriever using reformulation_prompt+llm+retriever
# 6. Create Stuff-Documents Chain using : LLM and qa_prompt.
# 6. Create history_aware_retrieval_chain using=> main history_aware_retriever+qa_stuff_documents_chain
# 7. Now wrap history_aware_retrieval_chain like: conversational_rag_chain = RunnableWithMessageHistory(
#             history_aware_retrieval_chain,
#             get_session_history,
#             input_messages_key="input",
#             history_messages_key="chat_history",
#             output_messages_key="answer"
#           ) 
# 8. While invoking conversational_rag_chain:
#             response = conversational_rag_chain.invoke(
#               {"input" : "What is Task Decomposition?"},
#               config= {"configurable" : {"session_id" : "abc123"}},
#             )

##=======================================================================
import streamlit as st
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import OllamaEmbeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain.chains import create_retrieval_chain, create_history_aware_retriever
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain.memory import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory

import os
from dotenv import load_dotenv

# --- ENVIRONMENT VARIABLES ---
load_dotenv()
os.environ['GROQ_API_KEY'] = os.getenv('GROQ_API_KEY')
os.environ['GOOGLE_API_KEY'] = os.getenv('GOOGLE_API_KEY')
os.environ['HF_TOKEN'] = os.getenv('HF_TOKEN')
os.environ['LANGCHAIN_API_KEY'] = os.getenv('LANGCHAIN_API_KEY')
os.environ['LANGSMITH_TRACING_V2'] = "true"
os.environ['LANGCHAIN_PROJECT'] = "History-Aware RAG with Groq + FAISS"

# --- STREAMLIT UI CONFIG ---
st.set_page_config(page_title="📄 History-Aware RAG Chatbot", page_icon="🤖")
st.title("📄 Conversational Retrieval-Augmented Q&A with Groq + FAISS")

st.sidebar.header("⚙️ Settings")

# --- SESSION MANAGEMENT ---
# Allow user to enter session ID (for memory persistence)
session_id = st.sidebar.text_input("Enter Session ID:", value="default_session")

# --- EMBEDDING SELECTION ---
embed_choice = st.sidebar.radio(
    "Choose embeddings:",
    (
        "Ollama (mxbai-embed-large)",
        "HuggingFace (all-MiniLM-L6-v2)",
        "Google Gemini (gemini-embedding-001)"
    )
)

if embed_choice == "Ollama (mxbai-embed-large)":
    embeddings = OllamaEmbeddings(model="mxbai-embed-large")
elif embed_choice == "HuggingFace (all-MiniLM-L6-v2)":
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
else:
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")

# --- LLM CONFIG ---
llm = ChatGroq(model="openai/gpt-oss-120b")

# --- PROMPTS ---
# Reformulation prompt: makes user queries standalone (context-independent)
reformulation_prompt = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(
        """Given a chat history and the latest user question which might reference context in the chat history. 
        Formulate a standalone question which can be understood without the chat history. 
        DO NOT answer the question, just reformulate it if needed and otherwise return it as is."""
    ),
    MessagesPlaceholder(variable_name="chat_history"),
    HumanMessagePromptTemplate.from_template("Question: {input}")
])

# QA prompt: instructs the LLM to answer using retrieved context
qa_prompt = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(
        "You are a helpful assistant. Use the following context to answer the question. "
        "If you don't know, say you don't know.\n\nContext: {context}"
    ),
    MessagesPlaceholder(variable_name="chat_history"),
    HumanMessagePromptTemplate.from_template("Question: {input}")
])

# --- VECTOR STORE CREATION ---
def create_vector_embeddings(pdf_path: str):
    """Load a PDF, split text, and store embeddings into FAISS vector DB."""
    loader = PyPDFLoader(pdf_path)
    docs = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    final_docs = text_splitter.split_documents(docs[:50])  # limit to 50 docs for speed
    st.session_state.vectors = FAISS.from_documents(final_docs, embeddings)
    st.session_state.retriever = st.session_state.vectors.as_retriever()
    st.success("✅ FAISS vector store created!")

# --- MEMORY MANAGEMENT ---
if "store" not in st.session_state:
    st.session_state.store = {}

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    """Retrieve or create chat history for a given session_id."""
    if session_id not in st.session_state.store:
        st.session_state.store[session_id] = ChatMessageHistory()
    return st.session_state.store[session_id]

# --- CHAT DISPLAY STATE ---
if "chat_display" not in st.session_state:
    st.session_state.chat_display = []

# --- FILE UPLOAD + VECTOR CREATION ---
pdf_file = st.file_uploader("📂 Upload a PDF file", type=["pdf"])

if pdf_file and st.button("📦 Create Vector Store"):
    # Save uploaded PDF temporarily
    pdf_path = f"./uploaded_{pdf_file.name}"
    with open(pdf_path, "wb") as f:
        f.write(pdf_file.getbuffer())
    create_vector_embeddings(pdf_path)

# --- CHAT WINDOW ---
st.subheader("💬 Chat with your PDF")

# Display chat history
for msg in st.session_state.chat_display:
    if msg["role"] == "user":
        st.markdown(f"**🧑 You:** {msg['content']}")
    else:
        st.markdown(f"**🤖 Assistant:** {msg['content']}")

# User input field
user_query = st.chat_input("Ask something about your PDF...")

if user_query:
    if "retriever" not in st.session_state:
        st.warning("⚠️ Please upload a PDF and click **📦 Create Vector Store** first.")
    else:
        # Append user message
        st.session_state.chat_display.append({"role": "user", "content": user_query})

        with st.spinner("🤔 Thinking..."):
            # Create history-aware retriever (reformulates queries with chat history)
            history_aware_retriever = create_history_aware_retriever(
                llm, st.session_state.retriever, reformulation_prompt
            )
            # Stuff retrieved docs into QA chain
            stuff_chain = create_stuff_documents_chain(llm, qa_prompt)
            # Combine retriever + QA chain
            history_aware_retrieval_chain = create_retrieval_chain(
                history_aware_retriever, stuff_chain
            )
            # Attach message history to chain
            conversational_rag_chain = RunnableWithMessageHistory(
                history_aware_retrieval_chain,
                get_session_history,
                input_messages_key="input",
                history_messages_key="chat_history",
                output_messages_key="answer"
            )

            # Run the chain with session-aware memory
            response = conversational_rag_chain.invoke(
                {"input": user_query},
                config={"configurable": {"session_id": session_id}},
            )

        # Append assistant response
        st.session_state.chat_display.append({"role": "assistant", "content": response["answer"]})
        st.rerun()