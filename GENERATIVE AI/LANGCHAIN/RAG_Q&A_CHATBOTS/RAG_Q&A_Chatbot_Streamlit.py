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
st.set_page_config(
    page_title="📄 History-Aware RAG Chatbot", 
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS FOR LIGHT MODE AND CHAT STYLING ---
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Main app styling for light mode */
    .stApp {
        background-color: #fafafa;
        font-family: 'Inter', sans-serif;
    }
    
    /* Sidebar Width Customization */
    [data-testid="stSidebar"] {
        width: 380px !important;
        min-width: 380px !important;
    }
    
    [data-testid="stSidebar"][aria-expanded="true"] > div:first-child {
        width: 380px;
        min-width: 380px;
        max-width: 380px;
    }
    
    [data-testid="stSidebar"][aria-expanded="false"] > div:first-child {
        width: 380px;
        min-width: 380px;
        max-width: 380px;
        margin-left: -380px;
    }
    
    /* Adjust main content area for wider sidebar */
    .main .block-container {
        padding-left: 2rem;
        padding-right: 2rem;
        max-width: none;
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
        backdrop-filter: blur(10px);
    }
    
    .main-header h1 {
        margin: 0;
        font-size: 2.2rem;
        font-weight: 700;
        letter-spacing: -0.02em;
    }
    
    .main-header p {
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
        font-size: 1rem;
    }
    
    /* Chat container */
    .chat-container {
        max-width: 900px;
        margin: 0 auto;
        padding: 1rem;
        background-color: white;
        border-radius: 12px;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
    }
    
    /* User message styling */
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 14px 18px;
        border-radius: 20px 20px 6px 20px;
        margin: 12px 0;
        margin-left: 25%;
        box-shadow: 0 4px 16px rgba(102, 126, 234, 0.3);
        position: relative;
        animation: slideInRight 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94);
        word-wrap: break-word;
    }
    
    /* Assistant message styling */
    .assistant-message {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        color: #2d3748;
        padding: 14px 18px;
        border-radius: 20px 20px 20px 6px;
        margin: 12px 0;
        margin-right: 25%;
        border-left: 4px solid #667eea;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
        position: relative;
        animation: slideInLeft 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94);
        word-wrap: break-word;
    }
    
    /* Message animations */
    @keyframes slideInRight {
        from { 
            transform: translateX(30px); 
            opacity: 0; 
        }
        to { 
            transform: translateX(0); 
            opacity: 1; 
        }
    }
    
    @keyframes slideInLeft {
        from { 
            transform: translateX(-30px); 
            opacity: 0; 
        }
        to { 
            transform: translateX(0); 
            opacity: 1; 
        }
    }
    
    /* Message labels */
    .message-label {
        font-size: 10px;
        font-weight: 600;
        margin-bottom: 6px;
        text-transform: uppercase;
        letter-spacing: 0.8px;
    }
    
    .user-label {
        color: rgba(255, 255, 255, 0.8);
        text-align: right;
    }
    
    .assistant-label {
        color: #667eea;
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #ffffff 0%, #f8f9ff 100%);
        border-right: 3px solid #e2e8f0;
        box-shadow: 4px 0 20px rgba(0, 0, 0, 0.08);
    }
    
    /* Sidebar headers */
    .sidebar-header {
        color: #4a5568;
        font-weight: 600;
        font-size: 1.1rem;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #e2e8f0;
    }
    
    /* Success message styling */
    .success-message {
        background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
        color: white;
        padding: 12px 16px;
        border-radius: 10px;
        margin: 1rem 0;
        box-shadow: 0 4px 16px rgba(72, 187, 120, 0.3);
        font-weight: 500;
    }
    
    /* Warning message styling */
    .warning-message {
        background: linear-gradient(135deg, #ed8936 0%, #dd6b20 100%);
        color: white;
        padding: 12px 16px;
        border-radius: 10px;
        margin: 1rem 0;
        box-shadow: 0 4px 16px rgba(237, 137, 54, 0.3);
        font-weight: 500;
    }
    
    /* File uploader styling */
    .stFileUploader {
        padding: 1rem;
        border: 2px dashed #667eea;
        border-radius: 12px;
        background-color: #f7fafc;
        transition: all 0.3s ease;
    }
    
    .stFileUploader:hover {
        border-color: #764ba2;
        background-color: #edf2f7;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        font-size: 0.95rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
        width: 100%;
        letter-spacing: 0.5px;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
        background: linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%);
    }
    
    /* Input field styling */
    .stTextInput > div > div > input {
        border: 2px solid #e2e8f0;
        border-radius: 10px;
        padding: 12px 16px;
        background-color: white;
        font-size: 0.95rem;
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1);
        outline: none;
    }
    
    /* Radio button styling */
    .stRadio > div {
        padding: 0.5rem 0;
    }
    
    .stRadio > div > label {
        font-weight: 500;
        color: #4a5568;
    }
    
    /* Metrics styling */
    .metric-container {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 1rem;
        border-radius: 10px;
        margin: 0.75rem 0;
        border-left: 4px solid #667eea;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    }
    
    /* Chat input styling */
    .stChatInput > div > div {
        border-radius: 25px;
        border: 2px solid #e2e8f0;
        background-color: white;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }
    
    .stChatInput > div > div:focus-within {
        border-color: #667eea;
        box-shadow: 0 4px 20px rgba(102, 126, 234, 0.2);
    }
    
    /* Spinner styling */
    .stSpinner > div {
        border-top-color: #667eea !important;
        border-width: 3px !important;
    }
    
    /* Info boxes */
    .stInfo {
        background-color: #ebf8ff;
        border-left: 4px solid #3182ce;
        padding: 1rem;
        border-radius: 8px;
    }
    
    /* Hide Streamlit default elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}
    header[data-testid="stHeader"] {display: none;}
    
    /* Responsive adjustments */
    @media (max-width: 768px) {
        [data-testid="stSidebar"] {
            width: 300px !important;
            min-width: 300px !important;
        }
        
        .chat-container {
            margin: 0.5rem;
            padding: 0.75rem;
        }
        
        .user-message, .assistant-message {
            margin-left: 10%;
            margin-right: 10%;
        }
    }
</style>
""", unsafe_allow_html=True)

# --- MAIN HEADER ---
st.markdown("""
<div class="main-header">
    <h1>📄 Conversational RAG Chatbot</h1>
    <p>Powered by Groq + FAISS | Enhanced with Memory</p>
</div>
""", unsafe_allow_html=True)

# --- SIDEBAR CONFIGURATION ---
st.sidebar.markdown('<div class="sidebar-header">⚙️ Configuration Panel</div>', unsafe_allow_html=True)

# --- SESSION MANAGEMENT ---
session_id = st.sidebar.text_input(
    "🔑 Session ID:", 
    value="default_session", 
    help="Enter a unique session ID to maintain conversation history"
)

# --- EMBEDDING SELECTION ---
st.sidebar.markdown('<div class="sidebar-header">🧠 Embedding Model Selection</div>', unsafe_allow_html=True)
embed_choice = st.sidebar.radio(
    "Choose your preferred embedding model:",
    (
        "Ollama (mxbai-embed-large)",
        "HuggingFace (all-MiniLM-L6-v2)",
        "Google Gemini (gemini-embedding-001)"
    ),
    help="Select the embedding model for document processing. Each has different performance characteristics."
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
reformulation_prompt = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(
        """Given a chat history and the latest user question which might reference context in the chat history. 
        Formulate a standalone question which can be understood without the chat history. 
        DO NOT answer the question, just reformulate it if needed and otherwise return it as is."""
    ),
    MessagesPlaceholder(variable_name="chat_history"),
    HumanMessagePromptTemplate.from_template("Question: {input}")
])

qa_prompt = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(
        "You are a helpful AI assistant. Use the following context to answer the question clearly and concisely. "
        "If you don't know the answer based on the context, say you don't know.\n\nContext: {context}"
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
    final_docs = text_splitter.split_documents(docs[:50])
    st.session_state.vectors = FAISS.from_documents(final_docs, embeddings)
    st.session_state.retriever = st.session_state.vectors.as_retriever()
    return True

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
st.sidebar.markdown("---")
st.sidebar.markdown('<div class="sidebar-header">📂 Document Management</div>', unsafe_allow_html=True)
pdf_file = st.sidebar.file_uploader(
    "Upload PDF Document", 
    type=["pdf"], 
    help="Upload a PDF document to create a knowledge base for chatting"
)

if pdf_file:
    st.sidebar.success(f"📄 **File:** {pdf_file.name}")
    if st.sidebar.button("📦 Process Document", help="Create vector embeddings from the uploaded PDF"):
        with st.sidebar:
            with st.spinner("Processing document..."):
                # Save uploaded PDF temporarily
                pdf_path = f"./uploaded_{pdf_file.name}"
                with open(pdf_path, "wb") as f:
                    f.write(pdf_file.getbuffer())
                
                if create_vector_embeddings(pdf_path):
                    st.markdown("""
                    <div class="success-message">
                        ✅ Document processed successfully! Ready to chat.
                    </div>
                    """, unsafe_allow_html=True)

# --- CHAT INTERFACE ---
st.markdown('<div class="chat-container">', unsafe_allow_html=True)

# Display chat history with custom styling
if st.session_state.chat_display:
    for i, msg in enumerate(st.session_state.chat_display):
        if msg["role"] == "user":
            st.markdown(f"""
            <div class="user-message">
                <div class="message-label user-label">You</div>
                {msg['content']}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="assistant-message">
                <div class="message-label assistant-label">AI Assistant</div>
                {msg['content']}
            </div>
            """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div style="text-align: center; padding: 2rem; color: #6b7280;">
        <h3>👋 Welcome to your AI Document Assistant!</h3>
        <p>Upload a PDF document and start asking questions to get intelligent answers.</p>
    </div>
    """, unsafe_allow_html=True)

# User input field
st.markdown("### 💬 Chat with your Document")
user_query = st.chat_input("Type your question here...", key="user_input")

if user_query:
    if "retriever" not in st.session_state:
        st.markdown("""
        <div class="warning-message">
            ⚠️ Please upload a PDF document and click "Process Document" first.
        </div>
        """, unsafe_allow_html=True)
    else:
        # Append user message
        st.session_state.chat_display.append({"role": "user", "content": user_query})

        # Display thinking spinner
        with st.spinner("🤔 AI is analyzing and thinking..."):
            try:
                # Create history-aware retriever
                history_aware_retriever = create_history_aware_retriever(
                    llm, st.session_state.retriever, reformulation_prompt
                )
                
                # Create document chain
                stuff_chain = create_stuff_documents_chain(llm, qa_prompt)
                
                # Create retrieval chain
                history_aware_retrieval_chain = create_retrieval_chain(
                    history_aware_retriever, stuff_chain
                )
                
                # Add message history
                conversational_rag_chain = RunnableWithMessageHistory(
                    history_aware_retrieval_chain,
                    get_session_history,
                    input_messages_key="input",
                    history_messages_key="chat_history",
                    output_messages_key="answer"
                )

                # Run the chain
                response = conversational_rag_chain.invoke(
                    {"input": user_query},
                    config={"configurable": {"session_id": session_id}},
                )

                # Append assistant response
                st.session_state.chat_display.append({"role": "assistant", "content": response["answer"]})
                
            except Exception as e:
                error_message = f"❌ An error occurred: {str(e)}"
                st.session_state.chat_display.append({"role": "assistant", "content": error_message})
        
        st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

# --- SIDEBAR STATS ---
st.sidebar.markdown("---")
st.sidebar.markdown('<div class="sidebar-header">📊 Session Statistics</div>', unsafe_allow_html=True)
if st.session_state.chat_display:
    total_messages = len(st.session_state.chat_display)
    user_messages = len([msg for msg in st.session_state.chat_display if msg["role"] == "user"])
    
    st.sidebar.markdown(f"""
    <div class="metric-container">
        <strong>📝 Total Messages:</strong> {total_messages}
    </div>
    """, unsafe_allow_html=True)
    
    st.sidebar.markdown(f"""
    <div class="metric-container">
        <strong>👤 Your Messages:</strong> {user_messages}
    </div>
    """, unsafe_allow_html=True)
else:
    st.sidebar.info("💡 Start chatting to see statistics")

# --- SIDEBAR CONTROLS ---
st.sidebar.markdown("---")
st.sidebar.markdown('<div class="sidebar-header">🛠️ Controls</div>', unsafe_allow_html=True)

# Clear chat button
if st.sidebar.button("🗑️ Clear Chat History", help="Clear all messages in current session"):
    st.session_state.chat_display = []
    if session_id in st.session_state.store:
        st.session_state.store[session_id] = ChatMessageHistory()
    st.success("Chat history cleared successfully!")
    st.rerun()

# Model info
st.sidebar.markdown("---")
st.sidebar.markdown('<div class="sidebar-header">ℹ️ Model Information</div>', unsafe_allow_html=True)
st.sidebar.markdown(f"""
**🤖 LLM:** Groq (gpt-oss-120b)  
**🧠 Embeddings:** {embed_choice.split('(')[0].strip()}  
**🗃️ Vector Store:** FAISS  
**💭 Memory:** Persistent Chat History  
**🔧 Framework:** LangChain
""")

# Additional info
st.sidebar.markdown("---")
st.sidebar.info("""
💡 **Tips:**
- Upload clear, text-based PDFs for best results
- Ask specific questions about your document
- Use follow-up questions to dive deeper
- Session history maintains context
""")
