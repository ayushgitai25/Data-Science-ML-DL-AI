"""
SQL DATABASE CHAT AGENT - COMPLETE WORKFLOW STEPS:

STEP 1: ENVIRONMENT & CONFIGURATION SETUP
    1.1. Load environment variables (.env file) for API keys
    1.2. Import required libraries (Streamlit, SQLAlchemy, LangChain)
    1.3. Set page configuration and apply light theme CSS styling

STEP 2: SESSION STATE INITIALIZATION  
    2.1. Initialize chat history storage (messages array)
    2.2. Set up database connection status tracking
    2.3. Store database URI and schema information
    2.4. Initialize query processing state management

STEP 3: DATABASE CONNECTION & INSPECTION
    3.1. Handle database type selection (SQLite or MySQL)
    3.2. Configure connection parameters based on user input
    3.3. Establish database connection using SQLAlchemy
    3.4. Inspect database schema to extract table and column information
    3.5. Store schema metadata in session state for query generation

STEP 4: SIDEBAR SETUP & UI CONFIGURATION
    4.1. Create database configuration interface
    4.2. Display database schema information in expandable sections
    4.3. Show connection status indicators
    4.4. Provide example query buttons for quick testing
    4.5. Add chat history management controls

STEP 5: NATURAL LANGUAGE TO SQL CONVERSION
    5.1. Accept user question in natural language
    5.2. Use LLM (Groq) to analyze question and database schema
    5.3. Generate appropriate SQL query based on database type (SQLite/MySQL)
    5.4. Apply database-specific syntax and best practices

STEP 6: QUERY EXECUTION & RESULTS HANDLING  
    6.1. Execute generated SQL query against the database
    6.2. Capture and format raw query results
    6.3. Handle query errors and edge cases
    6.4. Store execution metadata for display

STEP 7: RESULT INTERPRETATION & RESPONSE GENERATION
    7.1. Use LLM to interpret raw SQL results
    7.2. Convert technical results into natural language response
    7.3. Provide context-aware explanations
    7.4. Format response for user-friendly presentation
"""
import streamlit as st
from sqlalchemy import create_engine, inspect
import os
from dotenv import load_dotenv
from datetime import datetime

# Import LangChain components for database interaction
from langchain_community.utilities import SQLDatabase
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

# Load environment variables from .env file (for API keys)
load_dotenv()

# =============================================================================
# CONFIGURATION AND CONSTANTS
# =============================================================================

# Constants for database selection options
LOCALDB = "Use local SQLite database"
MYSQL = "Connect to MySQL database"

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def initialize_session_state():
    """
    Initialize Streamlit session state variables for maintaining chat history
    and database connection status across app reruns.
    """
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "db_connected" not in st.session_state:
        st.session_state.db_connected = False
        
    if "db_uri" not in st.session_state:
        st.session_state.db_uri = None
        
    if "schema_info" not in st.session_state:
        st.session_state.schema_info = {}
    
    # Track the last processed query to prevent duplicates
    if "last_processed_query" not in st.session_state:
        st.session_state.last_processed_query = None
    
    # Track message count to detect duplicates
    if "message_count" not in st.session_state:
        st.session_state.message_count = 0

def inspect_database_schema(db_uri):
    """
    Inspect and return database tables and their columns using SQLAlchemy.
    """
    try:
        engine = create_engine(db_uri)
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        schema_info = {}
        for table in tables:
            columns = inspector.get_columns(table)
            schema_info[table] = [column['name'] for column in columns]
        
        return schema_info
    except Exception as e:
        st.error(f"Error inspecting database schema: {e}")
        return {}

def generate_sql_query(user_question, schema_info, db_uri):
    """
    Generate SQL query from natural language question using LLM with database-specific syntax.
    """
    try:
        llm = ChatGroq(model_name="openai/gpt-oss-120b", temperature=0)
        
        # Determine database type from URI
        db_type = "SQLite" if "sqlite" in db_uri.lower() else "MySQL"
        
        # Database-specific syntax examples
        syntax_examples = {
            "SQLite": """
SQLite Syntax Examples:
- List tables: SELECT name FROM sqlite_master WHERE type='table';
- Table info: PRAGMA table_info(table_name);
- Count rows: SELECT COUNT(*) FROM table_name;
- Show data: SELECT * FROM table_name LIMIT 10;
""",
            "MySQL": """
MySQL Syntax Examples:
- List tables: SHOW TABLES;
- Table info: DESCRIBE table_name;
- Count rows: SELECT COUNT(*) FROM table_name;
- Show data: SELECT * FROM table_name LIMIT 10;
"""
        }
        
        sql_prompt = ChatPromptTemplate.from_template(
            """You are a SQL expert working with a {db_type} database. Given the following database schema and user question, 
            generate a precise SQL query that answers the question.
            
            Database Type: {db_type}
            {syntax_examples}
            
            Database Schema:
            {schema}
            
            User Question: {question}
            
            Rules:
            1. Generate only the SQL query, no explanations
            2. Use proper {db_type} syntax (NOT MySQL syntax if this is SQLite)
            3. Don't include markdown formatting or code blocks
            4. Limit results to 10 rows unless specifically asked for more
            5. Use appropriate WHERE clauses when needed
            6. For SQLite: Use sqlite_master table to get schema information
            7. For MySQL: Use SHOW commands and INFORMATION_SCHEMA
            
            SQL Query:"""
        )
        
        schema_text = "\n".join([
            f"Table: {table}\nColumns: {', '.join(columns)}\n" 
            for table, columns in schema_info.items()
        ])
        
        sql_chain = sql_prompt | llm
        response = sql_chain.invoke({
            "db_type": db_type,
            "syntax_examples": syntax_examples[db_type],
            "schema": schema_text,
            "question": user_question
        })
        
        sql_query = response.content.strip()
        sql_query = sql_query.replace("``````", "").strip()
        
        return sql_query
    
    except Exception as e:
        st.error(f"Error generating SQL query: {e}")
        return None

def execute_query_and_interpret(user_question, db_uri, schema_info):
    """
    Execute SQL query and interpret results using LLM to provide natural language response.
    """
    try:
        sql_query = generate_sql_query(user_question, schema_info, db_uri)  # Pass db_uri
        
        if not sql_query:
            return "Sorry, I couldn't generate a SQL query for your question.", None, None
        
        db = SQLDatabase.from_uri(db_uri)
        raw_results = db.run(sql_query)
        
        llm = ChatGroq(model_name="openai/gpt-oss-120b", temperature=0)
        
        interpretation_prompt = ChatPromptTemplate.from_template(
            """You are a helpful database assistant. Given the user's question, the SQL query that was executed, 
            and the query results, provide a clear and informative answer.
            
            User Question: {question}
            SQL Query Executed: {query}
            Query Results: {results}
            
            Rules:
            1. Provide a natural, conversational response
            2. If results are empty, say "No results found for your query"
            3. Format numbers and data clearly
            4. Be concise but informative
            5. Don't repeat the SQL query in your response
            
            Answer:"""
        )
        
        interpretation_chain = interpretation_prompt | llm
        response = interpretation_chain.invoke({
            "question": user_question,
            "query": sql_query,
            "results": raw_results
        })
        
        return response.content, sql_query, raw_results
        
    except Exception as e:
        error_msg = f"Error executing query: {str(e)}"
        return error_msg, sql_query if 'sql_query' in locals() else None, None

def add_message_to_chat(role, content, sql_query=None, raw_results=None):
    """
    Add a message to the chat history with duplicate prevention.
    """
    # Create a unique identifier for this message
    message_id = f"{role}_{content}_{datetime.now().strftime('%H:%M:%S:%f')}"
    
    # Check if this exact message was just added (prevent immediate duplicates)
    if (st.session_state.messages and 
        len(st.session_state.messages) > 0 and
        st.session_state.messages[-1]["content"] == content and
        st.session_state.messages[-1]["role"] == role):
        return  # Don't add duplicate
    
    message = {
        "id": message_id,
        "role": role,
        "content": content,
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "sql_query": sql_query,
        "raw_results": raw_results
    }
    st.session_state.messages.append(message)
    st.session_state.message_count += 1

def display_chat_message(message):
    """
    Display a single chat message with proper formatting.
    """
    if message["role"] == "user":
        with st.chat_message("user"):
            st.write(message["content"])
            st.caption(f"Sent at {message['timestamp']}")
    else:
        with st.chat_message("assistant"):
            st.write(message["content"])
            st.caption(f"Response at {message['timestamp']}")
            
            if message.get("sql_query"):
                with st.expander("🔍 View SQL Query"):
                    st.code(message["sql_query"], language="sql")
                    
            if message.get("raw_results"):
                with st.expander("📊 Raw Database Results"):
                    st.code(message["raw_results"])

def process_query(query_text):
    """
    Process a query with duplicate prevention.
    """
    # Prevent processing the same query multiple times
    query_key = f"{query_text}_{datetime.now().strftime('%H:%M:%S')}"
    
    if st.session_state.last_processed_query == query_key:
        return  # Already processed this query
    
    st.session_state.last_processed_query = query_key
    
    # Add user message to chat
    add_message_to_chat("user", query_text)
    
    # Execute query and get response
    answer, sql_query, raw_results = execute_query_and_interpret(
        query_text, 
        st.session_state.db_uri, 
        st.session_state.schema_info
    )
    
    # Add assistant response to chat history
    add_message_to_chat("assistant", answer, sql_query, raw_results)

# =============================================================================
# SIDEBAR CONFIGURATION
# =============================================================================

def setup_sidebar():
    """
    Setup the sidebar with database configuration options and connection status.
    """
    st.sidebar.header("🗄️ Database Configuration")
    
    # Database type selection
    db_choice = st.sidebar.radio(
        "Select Database Type:",
        (LOCALDB, MYSQL),
        help="Choose between local SQLite file or remote MySQL database"
    )
    
    db_uri = None
    
    # Configure SQLite connection
    if db_choice == LOCALDB:
        st.sidebar.subheader("SQLite Configuration")
        uploaded_file = st.sidebar.file_uploader(
            "Upload SQLite Database File",
            type=["db", "sqlite", "sqlite3"],
            help="Select a .db, .sqlite, or .sqlite3 file from your computer"
        )
        
        if uploaded_file is not None:
            temp_db_path = os.path.join(".", uploaded_file.name)
            with open(temp_db_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            db_uri = f"sqlite:///{temp_db_path}"
            st.sidebar.success(f"✅ Loaded: {uploaded_file.name}")
    
    # Configure MySQL connection
    elif db_choice == MYSQL:
        st.sidebar.subheader("MySQL Configuration")
        
        mysql_host = st.sidebar.text_input("Host", "localhost")
        mysql_user = st.sidebar.text_input("Username", "root")
        mysql_password = st.sidebar.text_input("Password", type="password")
        mysql_db = st.sidebar.text_input("Database Name")
        
        if all([mysql_host, mysql_user, mysql_password, mysql_db]):
            db_uri = f"mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}/{mysql_db}"
            st.sidebar.info("✅ MySQL connection configured")
    
    # Display database schema if connected
    if db_uri:
        try:
            schema_info = inspect_database_schema(db_uri)
            
            if schema_info:
                st.sidebar.subheader("📋 Database Schema")
                
                for table_name, columns in schema_info.items():
                    with st.sidebar.expander(f"📁 {table_name}"):
                        st.write("**Columns:**")
                        for col in columns:
                            st.write(f"• {col}")
                
                st.session_state.db_connected = True
                st.session_state.db_uri = db_uri
                st.session_state.schema_info = schema_info
                
                st.sidebar.success("🟢 Database Connected")
                
            else:
                st.sidebar.warning("⚠️ No tables found in database")
                st.session_state.db_connected = False
                
        except Exception as e:
            st.sidebar.error(f"❌ Connection Error: {e}")
            st.session_state.db_connected = False
            db_uri = None
    
    else:
        st.sidebar.info("📝 Please configure database connection")
        st.session_state.db_connected = False
    
    # Add clear chat history button
    st.sidebar.markdown("---")
    if st.sidebar.button("🗑️ Clear Chat History", help="Clear all chat messages"):
        st.session_state.messages = []
        st.session_state.message_count = 0
        st.session_state.last_processed_query = None
        st.rerun()
    
    # Display example queries if database is connected
    if st.session_state.db_connected and st.session_state.schema_info:
        st.sidebar.subheader("💡 Example Queries")
        st.sidebar.write("*Click to execute immediately*")
        tables = list(st.session_state.schema_info.keys())
        
        example_queries = [
            f"How many records are in the {tables[0]} table?",
            f"Show me the first 5 rows from {tables[0]}",
            "What tables are available in this database?",
            f"What columns does the {tables[0]} table have?",
        ]
        
        if len(tables) > 1:
            example_queries.extend([
                f"Show me the first 3 rows from {tables[1]}",
                f"How many records are in the {tables[1]} table?",
            ])
        
        # Use unique keys for each button and check if already processed
        for i, query in enumerate(example_queries[:6]):
            button_key = f"example_btn_{i}_{hash(query) % 10000}"
            if st.sidebar.button(
                f"▶️ {query}", 
                key=button_key,
                help="Click to execute this query",
                use_container_width=True
            ):
                process_query(query)
                st.rerun()
    
    return db_uri

# =============================================================================
# MAIN APPLICATION
# =============================================================================

def main():
    """
    Main application function that orchestrates the entire Streamlit app.
    """
    
    st.set_page_config(
        page_title="SQL Database Chat Agent",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # ☀️ COMPLETE LIGHT THEME CSS WITH ENHANCED CHAT MESSAGE COLORS
    st.markdown("""
    <style>
        /* Import Google Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        /* Root variables for light theme */
        :root {
            --primary-bg: #FFFFFF;
            --secondary-bg: #F8FAFC;
            --tertiary-bg: #F1F5F9;
            --accent-bg: #E2E8F0;
            --text-primary: #1E293B;
            --text-secondary: #475569;
            --text-muted: #64748B;
            --accent-color: #3B82F6;
            --success-color: #059669;
            --warning-color: #D97706;
            --error-color: #DC2626;
            --border-color: #CBD5E1;
            --hover-bg: #F1F5F9;
            --user-bg: #EBF8FF;
            --user-border: #3B82F6;
            --assistant-bg: #F0FDF4;
            --assistant-border: #10B981;
        }
        
        /* Main app styling */
        .stApp {
            background: linear-gradient(135deg, var(--primary-bg) 0%, #F8FAFC 100%) !important;
            color: var(--text-primary) !important;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        }
        
        /* Main content area */
        .main .block-container {
            background: rgba(255, 255, 255, 0.9) !important;
            border-radius: 12px !important;
            backdrop-filter: blur(10px) !important;
            border: 1px solid var(--border-color) !important;
            padding: 2rem !important;
            margin-top: 1rem !important;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1) !important;
        }
        
        /* Headers and text styling */
        h1, h2, h3, h4, h5, h6 {
            color: var(--text-primary) !important;
            font-weight: 600 !important;
        }
        
        h1 {
            background: linear-gradient(135deg, var(--accent-color), #1D4ED8) !important;
            -webkit-background-clip: text !important;
            -webkit-text-fill-color: transparent !important;
            background-clip: text !important;
        }
        
        p, div, span {
            color: var(--text-primary) !important;
        }
        
        /* Sidebar styling */
        section[data-testid="stSidebar"] {
            width: 450px !important;
            background: linear-gradient(180deg, var(--secondary-bg) 0%, var(--tertiary-bg) 100%) !important;
            border-right: 1px solid var(--border-color) !important;
        }
        
        .css-1d391kg {
            width: 450px !important;
            background: transparent !important;
        }
        
        /* Sidebar content */
        .sidebar .sidebar-content {
            background: transparent !important;
            padding: 1rem !important;
        }
        
        /* Sidebar headers */
        .sidebar h1, .sidebar h2, .sidebar h3 {
            color: var(--text-primary) !important;
            border-bottom: 2px solid var(--accent-color) !important;
            padding-bottom: 0.5rem !important;
            margin-bottom: 1rem !important;
        }
        
        /* Input fields */
        .stTextInput > div > div > input {
            background: var(--primary-bg) !important;
            color: var(--text-primary) !important;
            border: 1px solid var(--border-color) !important;
            border-radius: 8px !important;
            font-family: 'Inter', sans-serif !important;
        }
        
        .stTextInput > div > div > input:focus {
            border-color: var(--accent-color) !important;
            box-shadow: 0 0 0 1px var(--accent-color) !important;
        }
        
        /* Password input */
        input[type="password"] {
            background: var(--primary-bg) !important;
            color: var(--text-primary) !important;
            border: 1px solid var(--border-color) !important;
        }
        
        /* ========== ENHANCED FILE UPLOADER STYLING ========== */
        .stFileUploader {
            background: var(--tertiary-bg) !important;
            border: 2px dashed var(--border-color) !important;
            border-radius: 12px !important;
            padding: 1rem !important;
        }
        
        .stFileUploader:hover {
            border-color: var(--accent-color) !important;
            background: rgba(59, 130, 246, 0.05) !important;
        }
        
        /* File uploader content */
        .stFileUploader > div {
            background: transparent !important;
        }
        
        /* Drag and drop zone */
        .stFileUploader [data-testid="stFileUploaderDropzone"] {
            background: var(--primary-bg) !important;
            border: 2px dashed var(--border-color) !important;
            border-radius: 8px !important;
            color: var(--text-primary) !important;
            padding: 2rem !important;
            text-align: center !important;
            transition: all 0.3s ease !important;
        }
        
        .stFileUploader [data-testid="stFileUploaderDropzone"]:hover {
            border-color: var(--accent-color) !important;
            background: rgba(59, 130, 246, 0.08) !important;
            transform: scale(1.01) !important;
        }
        
        /* File uploader text */
        .stFileUploader label {
            color: var(--text-primary) !important;
            font-weight: 500 !important;
        }
        
        /* File uploader button */
        .stFileUploader button {
            background: linear-gradient(135deg, var(--accent-color) 0%, #1D4ED8 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 6px !important;
            padding: 0.5rem 1rem !important;
            font-weight: 500 !important;
            margin-top: 0.5rem !important;
            transition: all 0.3s ease !important;
        }
        
        .stFileUploader button:hover {
            background: linear-gradient(135deg, #1D4ED8 0%, var(--accent-color) 100%) !important;
            transform: translateY(-1px) !important;
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3) !important;
        }
        
        /* File uploader instructions */
        .stFileUploader small {
            color: var(--text-muted) !important;
            font-size: 0.8rem !important;
        }
        
        /* Uploaded file display */
        .uploadedFile {
            background: var(--tertiary-bg) !important;
            border: 1px solid var(--border-color) !important;
            border-radius: 8px !important;
            color: var(--text-primary) !important;
            padding: 0.5rem !important;
            margin-top: 0.5rem !important;
        }
        
        /* Radio buttons */
        .stRadio > div {
            background: var(--tertiary-bg) !important;
            border-radius: 8px !important;
            padding: 0.5rem !important;
            border: 1px solid var(--border-color) !important;
        }
        
        .stRadio > div > label {
            color: var(--text-primary) !important;
        }
        
        /* ========== LIGHT THEME BUTTONS WITH DARK TEXT ========== */
        .stButton > button {
            width: 100% !important;
            text-align: left !important;
            padding: 1rem !important;
            border-radius: 10px !important;
            border: 1px solid var(--border-color) !important;
            background: linear-gradient(135deg, #FFFFFF 0%, #F8FAFC 100%) !important;
            color: var(--text-primary) !important;  /* Dark text for visibility */
            font-size: 0.85rem !important;
            font-weight: 600 !important;  /* Bold for better readability */
            margin-bottom: 0.5rem !important;
            white-space: normal !important;
            height: auto !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1) !important;
        }
        
        .stButton > button:hover {
            background: linear-gradient(135deg, #F1F5F9 0%, #E2E8F0 100%) !important;
            border-color: var(--accent-color) !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.2) !important;
            color: var(--text-primary) !important;  /* Keep dark text on hover */
        }
        
        .stButton > button:active {
            transform: translateY(0px) !important;
            background: #E2E8F0 !important;
            color: var(--text-primary) !important;
        }
        
        .stButton > button:focus {
            outline: none !important;
            border-color: var(--accent-color) !important;
            box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.3) !important;
            color: var(--text-primary) !important;
        }
        
        .stButton > button:disabled {
            color: var(--text-muted) !important;
            background: #F8FAFC !important;
        }
        
        /* Ensure ALL text inside buttons is dark */
        .stButton button div {
            color: var(--text-primary) !important;
            font-weight: 600 !important;
        }
        
        .stButton button p {
            color: var(--text-primary) !important;
            font-weight: 600 !important;
        }
        
        .stButton button span {
            color: var(--text-primary) !important;
            font-weight: 600 !important;
        }
        
        /* Force all sidebar buttons to use dark text on light background */
        [data-testid="stSidebar"] .stButton > button {
            background: linear-gradient(135deg, #FFFFFF 0%, #F8FAFC 100%) !important;
            color: var(--text-primary) !important;
            border: 1px solid var(--border-color) !important;
            font-weight: 600 !important;
        }
        
        [data-testid="stSidebar"] .stButton > button:hover {
            background: linear-gradient(135deg, #F1F5F9 0%, #E2E8F0 100%) !important;
            border-color: var(--accent-color) !important;
            color: var(--text-primary) !important; 
        }
        
        /* Ensure text inside sidebar buttons is properly styled */
        [data-testid="stSidebar"] .stButton button * {
            color: var(--text-primary) !important;
            font-weight: 600 !important;
        }
        
        [data-testid="stSidebar"] .stButton button div {
            color: var(--text-primary) !important;
        }
        
        [data-testid="stSidebar"] .stButton button p {
            color: var(--text-primary) !important;
        }
        
        [data-testid="stSidebar"] .stButton button span {
            color: var(--text-primary) !important;
        }
        
        /* Clear Chat History button special styling */
        [data-testid="stSidebar"] .stButton > button[title*="Clear"] {
            background: linear-gradient(135deg, #FEF2F2 0%, #FEE2E2 100%) !important;
            color: var(--error-color) !important;
            border-color: #FECACA !important;
        }
        
        [data-testid="stSidebar"] .stButton > button[title*="Clear"]:hover {
            background: linear-gradient(135deg, #FEE2E2 0%, #FECACA 100%) !important;
            color: var(--error-color) !important;
        }
        
        /* Sidebar text and markdown */
        [data-testid="stSidebar"] .stMarkdown {
            color: var(--text-primary) !important;
        }
        
        [data-testid="stSidebar"] .stText {
            color: var(--text-primary) !important;
        }
        
        /* Success/Info/Warning/Error messages */
        .stSuccess {
            background: rgba(16, 185, 129, 0.1) !important;
            color: var(--success-color) !important;
            border: 1px solid var(--success-color) !important;
            border-radius: 8px !important;
        }
        
        .stInfo {
            background: rgba(59, 130, 246, 0.1) !important;
            color: var(--accent-color) !important;
            border: 1px solid var(--accent-color) !important;
            border-radius: 8px !important;
        }
        
        .stWarning {
            background: rgba(217, 119, 6, 0.1) !important;
            color: var(--warning-color) !important;
            border: 1px solid var(--warning-color) !important;
            border-radius: 8px !important;
        }
        
        .stError {
            background: rgba(220, 38, 38, 0.1) !important;
            color: var(--error-color) !important;
            border: 1px solid var(--error-color) !important;
            border-radius: 8px !important;
        }
        
        /* ========== ENHANCED CHAT MESSAGE STYLING WITH DIFFERENT COLORS ========== */
        
        /* Base chat message styling */
        .stChatMessage {
            border-radius: 12px !important;
            margin-bottom: 1rem !important;
            backdrop-filter: blur(5px) !important;
            padding: 1rem !important;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1) !important;
            transition: all 0.3s ease !important;
        }
        
        /* User (Human) Messages - Light Blue Theme */
        [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
            background: linear-gradient(135deg, var(--user-bg) 0%, #DBEAFE 100%) !important;
            border: 1px solid #93C5FD !important;
            border-left: 4px solid var(--user-border) !important;
        }
        
        /* Assistant (AI) Messages - Light Green Theme */  
        [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) {
            background: linear-gradient(135deg, var(--assistant-bg) 0%, #DCFCE7 100%) !important;
            border: 1px solid #86EFAC !important;
            border-left: 4px solid var(--assistant-border) !important;
        }
        
        /* Chat message hover effects */
        .stChatMessage:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important;
        }
        
        /* Chat message content */
        [data-testid="stChatMessageContent"] {
            color: var(--text-primary) !important;
            font-size: 0.95rem !important;
            line-height: 1.6 !important;
        }
        
        [data-testid="stChatMessageContent"] p {
            color: var(--text-primary) !important;
            margin: 0.5rem 0 !important;
        }
        
        /* Avatar customization */
        [data-testid="stChatMessageAvatarUser"] {
            background: linear-gradient(135deg, var(--user-border) 0%, #1D4ED8 100%) !important;
            color: white !important;
            font-weight: 600 !important;
            border: 2px solid white !important;
            box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3) !important;
        }
        
        [data-testid="stChatMessageAvatarAssistant"] {
            background: linear-gradient(135deg, var(--assistant-border) 0%, #059669 100%) !important;
            color: white !important;
            font-weight: 600 !important;
            border: 2px solid white !important;
            box-shadow: 0 2px 8px rgba(16, 185, 129, 0.3) !important;
        }
        
        /* Chat input */
        .stChatInput > div {
            background: var(--primary-bg) !important;
            border: 1px solid var(--border-color) !important;
            border-radius: 12px !important;
        }
        
        .stChatInput input {
            background: transparent !important;
            color: var(--text-primary) !important;
            font-size: 1rem !important;
        }
        
        .stChatInput input::placeholder {
            color: var(--text-muted) !important;
        }
        
        /* Expanders */
        .streamlit-expanderHeader {
            background: var(--tertiary-bg) !important;
            color: var(--text-primary) !important;
            border: 1px solid var(--border-color) !important;
            border-radius: 8px !important;
            font-weight: 500 !important;
        }
        
        .streamlit-expanderContent {
            background: var(--secondary-bg) !important;
            border: 1px solid var(--border-color) !important;
            border-top: none !important;
            border-radius: 0 0 8px 8px !important;
        }
        
        /* Code blocks */
        .stCode {
            background: var(--tertiary-bg) !important;
            border: 1px solid var(--border-color) !important;
            border-radius: 8px !important;
            color: var(--text-primary) !important;
        }
        
        /* Scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: var(--secondary-bg);
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb {
            background: var(--accent-color);
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: #1D4ED8;
        }
        
        /* Caption text */
        .caption {
            color: var(--text-muted) !important;
            font-size: 0.8rem !important;
            font-style: italic !important;
        }
        
        /* Loading spinner */
        .stSpinner {
            color: var(--accent-color) !important;
        }
        
        /* Markdown content */
        .markdown-text-container {
            color: var(--text-primary) !important;
        }
        
        /* Links */
        a {
            color: var(--accent-color) !important;
            text-decoration: none !important;
        }
        
        a:hover {
            color: #1D4ED8 !important;
            text-decoration: underline !important;
        }
        
        /* Custom gradient background for the main title area */
        .title-container {
            background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(29, 78, 216, 0.1) 100%) !important;
            border-radius: 12px !important;
            padding: 1rem !important;
            margin-bottom: 2rem !important;
            border: 1px solid rgba(59, 130, 246, 0.2) !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
    initialize_session_state()
    db_uri = setup_sidebar()
    
    # Wrap title in custom container
    st.markdown('<div class="title-container">', unsafe_allow_html=True)
    st.title("🤖 SQL Database Chat Agent")
    st.markdown("Ask questions about your database in natural language!")
    st.markdown('</div>', unsafe_allow_html=True)
    
    if not st.session_state.db_connected:
        st.info("👈 Please configure your database connection in the wider sidebar to start chatting.")
        
        st.markdown("""
        ### How to use:
        1. **Configure Database**: Upload a SQLite file or enter MySQL credentials in the sidebar
        2. **View Schema**: Check the database tables and columns in the sidebar
        3. **Try Examples**: Click example queries in the sidebar to execute them immediately
        4. **Ask Questions**: Use the chat input below to ask natural language questions
        5. **Get Answers**: The AI will generate SQL queries and provide answers
        """)
        return
    
    # Display chat history
    chat_container = st.container()
    
    with chat_container:
        for message in st.session_state.messages:
            display_chat_message(message)
    
    # Chat input at the bottom
    if prompt := st.chat_input("Ask a question about your database..."):
        process_query(prompt)
        st.rerun()

if __name__ == "__main__":
    main()
