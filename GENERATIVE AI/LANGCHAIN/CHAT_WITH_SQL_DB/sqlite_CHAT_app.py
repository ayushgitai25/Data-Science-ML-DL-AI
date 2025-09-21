"""
SQL DATABASE CHAT AGENT - COMPLETE WORKFLOW STEPS:

STEP 1: ENVIRONMENT & CONFIGURATION SETUP
    1.1. Load environment variables (.env file) for API keys
    1.2. Import required libraries (Streamlit, SQLAlchemy, LangChain)
    1.3. Set page configuration and apply beautiful gradient-based dark+light theme CSS styling

STEP 2: SESSION STATE INITIALIZATION  
    2.1. Initialize chat history storage (messages array)
    2.2. Set up database connection status tracking
    2.3. Store database URI and schema information
    2.4. Initialize query processing state management
    2.5. Initialize AI model selection state

STEP 3: AI MODEL CONFIGURATION & SELECTION
    3.1. Define available Groq models with specifications
    3.2. Provide model selection interface in sidebar
    3.3. Store selected model in session state
    3.4. Configure LLM with user-selected model

STEP 4: DATABASE CONNECTION & INSPECTION
    4.1. Handle database type selection (SQLite or MySQL)
    4.2. Configure connection parameters based on user input
    4.3. Establish database connection using SQLAlchemy
    4.4. Inspect database schema to extract table and column information
    4.5. Store schema metadata in session state for query generation

STEP 5: SIDEBAR SETUP & UI CONFIGURATION
    5.1. Create AI model selection interface
    5.2. Create database configuration interface
    5.3. Display database schema information in expandable sections
    5.4. Show connection status indicators
    5.5. Provide example query buttons for quick testing
    5.6. Add chat history management controls

STEP 6: NATURAL LANGUAGE TO SQL CONVERSION
    6.1. Accept user question in natural language
    6.2. Use selected LLM (Groq) to analyze question and database schema
    6.3. Generate appropriate SQL query based on database type (SQLite/MySQL)
    6.4. Apply database-specific syntax and best practices

STEP 7: QUERY EXECUTION & RESULTS HANDLING  
    7.1. Execute generated SQL query against the database
    7.2. Capture and format raw query results
    7.3. Handle query errors and edge cases
    7.4. Store execution metadata for display

STEP 8: RESULT INTERPRETATION & RESPONSE GENERATION
    8.1. Use selected LLM to interpret raw SQL results
    8.2. Convert technical results into natural language response
    8.3. Provide context-aware explanations
    8.4. Format response for user-friendly presentation
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

# GROQ MODEL CONFIGURATION - Multiple AI models for flexible selection
GROQ_MODELS = {
    # Production Models (Recommended)
    "🚀 Llama 3.1 8B (Fast)": {
        "id": "llama-3.1-8b-instant", 
        "context": "131K", 
        "description": "Ultra-fast model, perfect for quick SQL generation",
        "category": "production",
        "speed": "⚡ Ultra-fast",
        "cost": "💰 Low"
    },
    "🧠 Llama 3.3 70B (Smart)": {
        "id": "llama-3.3-70b-versatile", 
        "context": "131K", 
        "description": "Best balance of speed and SQL accuracy",
        "category": "production",
        "speed": "⚡ Fast",
        "cost": "💰 Medium"
    },
    "🔥 GPT-OSS 120B (Premium)": {
        "id": "openai/gpt-oss-120b", 
        "context": "131K", 
        "description": "Premium model with superior SQL reasoning",
        "category": "production",
        "speed": "⚡ Fast",
        "cost": "💰 High"
    },
    "⭐ GPT-OSS 20B (Balanced)": {
        "id": "openai/gpt-oss-20b", 
        "context": "131K", 
        "description": "Balanced performance for database queries",
        "category": "production",
        "speed": "⚡ Very Fast",
        "cost": "💰 Medium"
    },
    
    # Preview Models (Advanced)
    "🔬 Llama 4 Maverick 17B": {
        "id": "meta-llama/llama-4-maverick-17b-128e-instruct", 
        "context": "131K", 
        "description": "Experimental next-gen SQL generation",
        "category": "preview",
        "speed": "⚡ Fast",
        "cost": "💰 Medium"
    },
    "🌙 Kimi K2 Instruct": {
        "id": "moonshotai/kimi-k2-instruct-0905", 
        "context": "262K", 
        "description": "Ultra-long context for complex database schemas",
        "category": "preview",
        "speed": "⚡ Medium",
        "cost": "💰 High"
    },
    "🤖 Qwen3 32B": {
        "id": "qwen/qwen3-32b", 
        "context": "131K", 
        "description": "Multilingual database query specialist",
        "category": "preview",
        "speed": "⚡ Fast",
        "cost": "💰 Medium"
    }
}

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def initialize_session_state():
    """
    Initialize Streamlit session state variables for maintaining chat history,
    database connection status, and AI model selection across app reruns.
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
    
    # AI Model selection state
    if "selected_model" not in st.session_state:
        st.session_state.selected_model = "🧠 Llama 3.3 70B (Smart)"  # Default to balanced model

def get_selected_llm():
    """
    STEP 3.4: Initialize the selected Groq LLM model
    - Gets user's selected model from session state
    - Creates ChatGroq instance with temperature=0 (deterministic for SQL)
    - Returns configured LLM ready for SQL generation and interpretation
    """
    model_config = GROQ_MODELS[st.session_state.selected_model]
    return ChatGroq(
        model=model_config["id"],
        temperature=0,  # Deterministic output for consistent SQL generation
        max_tokens=None,
        timeout=None,
        max_retries=2
    )

def inspect_database_schema(db_uri):
    """
    STEP 4.4: Inspect and return database tables and their columns using SQLAlchemy.
    - Connects to database using provided URI
    - Extracts all table names and their column information
    - Returns structured schema dictionary for SQL generation
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
    STEP 6: Generate SQL query from natural language question using selected LLM
    - Uses user-selected Groq model for SQL generation
    - Applies database-specific syntax (SQLite vs MySQL)
    - Incorporates database schema information
    - Returns precise SQL query string
    """
    try:
        llm = get_selected_llm()  # Use selected model
        
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
    STEP 7 & 8: Execute SQL query and interpret results using selected LLM
    - Generates SQL using user question and schema
    - Executes query against database
    - Uses selected LLM to interpret results into natural language
    - Returns formatted response with SQL and raw results
    """
    try:
        sql_query = generate_sql_query(user_question, schema_info, db_uri)
        
        if not sql_query:
            return "Sorry, I couldn't generate a SQL query for your question.", None, None
        
        db = SQLDatabase.from_uri(db_uri)
        raw_results = db.run(sql_query)
        
        llm = get_selected_llm()  # Use selected model for interpretation
        
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
        "raw_results": raw_results,
        "model_used": st.session_state.selected_model if role == "assistant" else None
    }
    st.session_state.messages.append(message)
    st.session_state.message_count += 1

def display_chat_message(message):
    """
    Display a single chat message with proper formatting and model information.
    """
    if message["role"] == "user":
        with st.chat_message("user"):
            st.write(message["content"])
            st.caption(f"Sent at {message['timestamp']}")
    else:
        with st.chat_message("assistant"):
            st.write(message["content"])
            
            # Show which model was used for this response
            model_used = message.get("model_used", "Unknown Model")
            st.caption(f"Response at {message['timestamp']} • Model: {model_used}")
            
            if message.get("sql_query"):
                with st.expander("🔍 View Generated SQL Query"):
                    st.code(message["sql_query"], language="sql")
                    
            if message.get("raw_results"):
                with st.expander("📊 Raw Database Results"):
                    st.code(message["raw_results"])

def process_query(query_text):
    """
    Process a query with duplicate prevention and model tracking.
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
    STEP 5: Setup the sidebar with AI model selection, database configuration, 
    and connection status display.
    """
    # STEP 5.1: AI Model Selection Interface
    st.sidebar.markdown("""
    <div class="sidebar-header">
        <h2 style="margin: 0; font-family: 'Poppins', sans-serif; font-weight: 600;">🤖 AI Model Selection</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Group models by category
    production_models = [k for k, v in GROQ_MODELS.items() if v['category'] == 'production']
    preview_models = [k for k, v in GROQ_MODELS.items() if v['category'] == 'preview']
    
    st.sidebar.markdown("#### 🚀 **Production Models** (Recommended)")
    for model_name in production_models:
        model_info = GROQ_MODELS[model_name]
        if st.sidebar.button(
            f"{model_name}",
            key=f"model_{model_name}",
            help=f"{model_info['description']} • Context: {model_info['context']} • {model_info['speed']} • {model_info['cost']}",
            use_container_width=True
        ):
            st.session_state.selected_model = model_name
            st.rerun()
        
        # Show selection indicator
        if st.session_state.selected_model == model_name:
            st.sidebar.markdown(f'''
            <div class="model-selection-indicator success">
                ✅ <strong>Selected:</strong> {model_info['description']}<br>
                <small>{model_info['speed']} • {model_info['cost']} • Context: {model_info['context']}</small>
            </div>
            ''', unsafe_allow_html=True)
    
    st.sidebar.markdown("#### 🔬 **Preview Models** (Experimental)")
    with st.sidebar.expander("Show Preview Models", expanded=False):
        for model_name in preview_models:
            model_info = GROQ_MODELS[model_name]
            if st.sidebar.button(
                f"{model_name}",
                key=f"model_preview_{model_name}",
                help=f"{model_info['description']} • Context: {model_info['context']} • {model_info['speed']} • {model_info['cost']}",
                use_container_width=True
            ):
                st.session_state.selected_model = model_name
                st.rerun()
            
            # Show selection indicator for preview models
            if st.session_state.selected_model == model_name:
                st.sidebar.markdown(f'''
                <div class="model-selection-indicator warning">
                    ⚠️ <strong>Preview Selected:</strong> {model_info['description']}<br>
                    <small>{model_info['speed']} • {model_info['cost']} • Context: {model_info['context']}</small>
                </div>
                ''', unsafe_allow_html=True)
    
    st.sidebar.markdown("---")
    
    # STEP 5.2: Database Configuration Interface
    st.sidebar.markdown("""
    <div class="sidebar-header" style="margin-top: 1.5rem;">
        <h2 style="margin: 0; font-family: 'Poppins', sans-serif; font-weight: 600;">🗄️ Database Configuration</h2>
    </div>
    """, unsafe_allow_html=True)
    
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
    
    # STEP 5.3: Display database schema if connected
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
                
                st.sidebar.markdown('<div class="status-indicator success">🟢 Database Connected</div>', unsafe_allow_html=True)
                
            else:
                st.sidebar.markdown('<div class="status-indicator warning">⚠️ No tables found in database</div>', unsafe_allow_html=True)
                st.session_state.db_connected = False
                
        except Exception as e:
            st.sidebar.markdown(f'<div class="status-indicator error">❌ Connection Error: {str(e)}</div>', unsafe_allow_html=True)
            st.session_state.db_connected = False
            db_uri = None
    
    else:
        st.sidebar.markdown('<div class="status-indicator info">📝 Please configure database connection</div>', unsafe_allow_html=True)
        st.session_state.db_connected = False
    
    # STEP 5.6: Add clear chat history button
    st.sidebar.markdown("---")
    if st.sidebar.button("🗑️ Clear Chat History", help="Clear all chat messages"):
        st.session_state.messages = []
        st.session_state.message_count = 0
        st.session_state.last_processed_query = None
        st.rerun()
    
    # STEP 5.5: Display example queries if database is connected
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
    Main application function that orchestrates the entire Streamlit app
    with corrected beautiful gradient backgrounds and PERFECT chat message text visibility.
    """
    
    st.set_page_config(
        page_title="SQL Database Chat Agent",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # CORRECTED BEAUTIFUL GRADIENT-BASED CSS WITH PERFECT CHAT MESSAGE TEXT VISIBILITY
    st.markdown("""
    <style>
        /* Import Google Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Poppins:wght@300;400;500;600;700&display=swap');
        
        /* Hide default streamlit styling */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        .stDeployButton {display:none;}
        
        /* Enable color-scheme support for system theme detection */
        :root {
            color-scheme: light dark;
        }
        
        /* WIDER SIDEBAR - 480px for model selection */
        section[data-testid="stSidebar"] {
            width: 480px !important;
            min-width: 480px !important;
        }
        
        section[data-testid="stSidebar"] > div:first-child {
            width: 480px !important;
            min-width: 480px !important;
        }
        
        section[data-testid="stSidebar"][aria-expanded="true"] > div:first-child {
            width: 480px !important;
            margin-left: 0px !important;
        }
        
        section[data-testid="stSidebar"][aria-expanded="false"] > div:first-child {
            width: 480px !important;
            margin-left: -480px !important;
        }
        
        /* Adjust main content area to account for wider sidebar */
        .main .block-container {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            max-width: none !important;
        }
        
        /* LIGHT THEME STYLES (Default) */
        .main-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 2.5rem 2rem;
            border-radius: 20px;
            margin-bottom: 2rem;
            text-align: center;
            color: #ffffff;
            box-shadow: 0 10px 40px rgba(31, 38, 135, 0.4);
            backdrop-filter: blur(10px);
        }
        
        .main-header h1 {
            font-family: 'Poppins', sans-serif;
            font-weight: 700;
            font-size: 2.8rem;
            margin: 0;
            color: #ffffff !important;
            text-shadow: 2px 2px 8px rgba(0,0,0,0.5);
            letter-spacing: -0.5px;
        }
        
        .main-header p {
            font-family: 'Inter', sans-serif;
            font-weight: 400;
            font-size: 1.3rem;
            margin: 1rem 0 0 0;
            color: #ffffff !important;
            opacity: 1;
            max-width: 600px;
            margin-left: auto;
            margin-right: auto;
            text-shadow: 1px 1px 4px rgba(0,0,0,0.4);
        }
        
        /* Step sections with enhanced styling - LIGHT THEME */
        .step-container {
            background: linear-gradient(145deg, #ffffff 0%, #f8faff 100%);
            border-radius: 16px;
            padding: 2rem;
            margin: 2rem 0;
            border: 1px solid #e8ecf7;
            box-shadow: 0 8px 32px rgba(102, 126, 234, 0.08);
            position: relative;
            overflow: hidden;
            color: #0f172a;
        }
        
        .step-container::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, #667eea, #764ba2);
        }
        
        /* FIXED: Force dark text in step containers */
        .step-container strong {
            color: #0f172a !important;
            font-weight: 700 !important;
        }
        
        .step-container small {
            color: #475569 !important;
            font-weight: 500 !important;
        }
        
        /* Enhanced status indicators with gradients - LIGHT THEME */
        .status-indicator {
            padding: 1rem 1.5rem;
            border-radius: 12px;
            margin: 1rem 0;
            font-family: 'Inter', sans-serif;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 0.75rem;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        }
        
        .status-indicator.success {
            background: linear-gradient(135deg, #10b981, #059669);
            color: white;
        }
        
        .status-indicator.error {
            background: linear-gradient(135deg, #ef4444, #dc2626);
            color: white;
        }
        
        .status-indicator.info {
            background: linear-gradient(135deg, #3b82f6, #2563eb);
            color: white;
        }
        
        .status-indicator.warning {
            background: linear-gradient(135deg, #f59e0b, #d97706);
            color: white;
        }
        
        /* Model selection indicators - LIGHT THEME */
        .model-selection-indicator {
            padding: 0.8rem;
            border-radius: 12px;
            margin: 0.5rem 0;
            font-family: 'Inter', sans-serif;
            font-size: 0.85rem;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        }
        
        .model-selection-indicator.success {
            background: linear-gradient(135deg, #10b981, #059669);
            color: white;
        }
        
        .model-selection-indicator.warning {
            background: linear-gradient(135deg, #f59e0b, #d97706);
            color: white;
        }
        
        /* Sidebar headers with gradients - LIGHT THEME */
        .sidebar-header {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: #ffffff !important;
            padding: 1.5rem;
            border-radius: 16px;
            margin-bottom: 1.5rem;
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
            text-align: center;
        }
        
        .sidebar-header h2 {
            color: #ffffff !important;
            text-shadow: 1px 1px 3px rgba(0,0,0,0.3);
        }
        
        /* Enhanced Buttons with gradients - LIGHT THEME */
        .stButton > button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #ffffff !important;
            border: none;
            border-radius: 12px;
            padding: 0.75rem 2rem;
            font-family: 'Inter', sans-serif;
            font-weight: 500;
            font-size: 1rem;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.3);
            width: 100%;
            min-height: 48px;
        }
        
        .stButton > button:hover {
            transform: translateY(-3px);
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
            background: linear-gradient(135deg, #5a72e8 0%, #6d42a0 100%);
            color: #ffffff !important;
        }
        
        .stButton > button:active {
            transform: translateY(-1px);
        }
        
        /* ========== CRITICAL FIX: CHAT MESSAGE TEXT VISIBILITY ========== */
        
        /* ENHANCED CHAT MESSAGE STYLING WITH PERFECT TEXT CONTRAST */
        .stChatMessage {
            border-radius: 16px !important;
            margin-bottom: 1.5rem !important;
            backdrop-filter: blur(10px) !important;
            padding: 1.5rem !important;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1) !important;
            transition: all 0.3s ease !important;
            position: relative !important;
            overflow: hidden !important;
        }
        
        /* User (Human) Messages - FIXED: Dark text on light blue background for maximum contrast */
        [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
            background: linear-gradient(135deg, #ebf8ff 0%, #dbeafe 100%) !important;
            border: 1px solid #93c5fd !important;
            border-left: 4px solid #3b82f6 !important;
            color: #0f172a !important;  /* FIXED: Very dark text for maximum contrast */
        }
        
        /* FIXED: Force dark text in ALL content within user messages */
        [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) * {
            color: #0f172a !important;
        }
        
        [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) p {
            color: #0f172a !important;
        }
        
        [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) div {
            color: #0f172a !important;
        }
        
        [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stChatMessageContent"] {
            color: #0f172a !important;
        }
        
        [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stChatMessageContent"] * {
            color: #0f172a !important;
        }
        
        [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"])::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 2px;
            background: linear-gradient(90deg, #3b82f6, #1d4ed8);
        }
        
        /* Assistant (AI) Messages - FIXED: Dark text on light green background for maximum contrast */
        [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) {
            background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%) !important;
            border: 1px solid #86efac !important;
            border-left: 4px solid #10b981 !important;
            color: #0f172a !important;  /* FIXED: Very dark text for maximum contrast */
        }
        
        /* FIXED: Force dark text in ALL content within assistant messages */
        [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) * {
            color: #0f172a !important;
        }
        
        [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) p {
            color: #0f172a !important;
        }
        
        [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) div {
            color: #0f172a !important;
        }
        
        [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) [data-testid="stChatMessageContent"] {
            color: #0f172a !important;
        }
        
        [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) [data-testid="stChatMessageContent"] * {
            color: #0f172a !important;
        }
        
        [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"])::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 2px;
            background: linear-gradient(90deg, #10b981, #059669);
        }
        
        /* Chat message hover effects */
        .stChatMessage:hover {
            transform: translateY(-4px) !important;
            box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15) !important;
        }
        
        /* Avatar customization with gradients */
        [data-testid="stChatMessageAvatarUser"] {
            background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%) !important;
            color: white !important;
            font-weight: 600 !important;
            border: 3px solid white !important;
            box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4) !important;
        }
        
        [data-testid="stChatMessageAvatarAssistant"] {
            background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
            color: white !important;
            font-weight: 600 !important;
            border: 3px solid white !important;
            box-shadow: 0 4px 15px rgba(16, 185, 129, 0.4) !important;
        }
        
        /* DARK THEME ADAPTATIONS - WITH FIXED CHAT MESSAGE TEXT */
        @media (prefers-color-scheme: dark) {
            /* Main header - Better contrast for dark theme */
            .main-header {
                background: linear-gradient(135deg, #4c1d95 0%, #6366f1 100%);
                box-shadow: 0 10px 40px rgba(76, 29, 149, 0.4);
                color: #ffffff !important;
            }
            
            .main-header h1 {
                color: #ffffff !important;
                text-shadow: 2px 2px 8px rgba(0,0,0,0.7);
            }
            
            .main-header p {
                color: #ffffff !important;
                text-shadow: 1px 1px 4px rgba(0,0,0,0.6);
            }
            
            /* Step containers - Better contrast for readability */
            .step-container {
                background: linear-gradient(145deg, #1f2937 0%, #111827 100%);
                border-color: #374151;
                color: #f9fafb !important;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            }
            
            .step-container::before {
                background: linear-gradient(90deg, #6366f1, #8b5cf6);
            }
            
            /* FIXED: Force light text in dark step containers */
            .step-container strong {
                color: #f9fafb !important;
                font-weight: 700 !important;
            }
            
            .step-container small {
                color: #d1d5db !important;
                font-weight: 500 !important;
            }
            
            /* Sidebar headers - Improved contrast */
            .sidebar-header {
                background: linear-gradient(135deg, #4c1d95, #6366f1);
                box-shadow: 0 8px 25px rgba(76, 29, 149, 0.4);
                color: #ffffff !important;
            }
            
            .sidebar-header h2 {
                color: #ffffff !important;
                text-shadow: 1px 1px 3px rgba(0,0,0,0.5);
            }
            
            /* Buttons - Better visibility in dark mode */
            .stButton > button {
                background: linear-gradient(135deg, #4c1d95 0%, #6366f1 100%);
                box-shadow: 0 6px 20px rgba(76, 29, 149, 0.4);
                color: #ffffff !important;
            }
            
            .stButton > button:hover {
                background: linear-gradient(135deg, #3730a3 0%, #4338ca 100%);
                box-shadow: 0 8px 25px rgba(76, 29, 149, 0.5);
                color: #ffffff !important;
            }
            
            /* DARK THEME CHAT MESSAGES - FIXED TEXT VISIBILITY */
            
            /* User messages in dark theme - Light text on dark blue */
            [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
                background: linear-gradient(135deg, #1e3a8a 0%, #1d4ed8 100%) !important;
                border-color: #3b82f6 !important;
                color: #f0f9ff !important;  /* FIXED: Light text for dark background */
            }
            
            /* FIXED: Force light text in ALL content within user messages (dark theme) */
            [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) * {
                color: #f0f9ff !important;
            }
            
            [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) p {
                color: #f0f9ff !important;
            }
            
            [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) div {
                color: #f0f9ff !important;
            }
            
            [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stChatMessageContent"] {
                color: #f0f9ff !important;
            }
            
            [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stChatMessageContent"] * {
                color: #f0f9ff !important;
            }
            
            /* Assistant messages in dark theme - Light text on dark green */
            [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) {
                background: linear-gradient(135deg, #064e3b 0%, #047857 100%) !important;
                border-color: #10b981 !important;
                color: #ecfdf5 !important;  /* FIXED: Light text for dark background */
            }
            
            /* FIXED: Force light text in ALL content within assistant messages (dark theme) */
            [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) * {
                color: #ecfdf5 !important;
            }
            
            [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) p {
                color: #ecfdf5 !important;
            }
            
            [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) div {
                color: #ecfdf5 !important;
            }
            
            [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) [data-testid="stChatMessageContent"] {
                color: #ecfdf5 !important;
            }
            
            [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) [data-testid="stChatMessageContent"] * {
                color: #ecfdf5 !important;
            }
            
            /* Other dark theme elements */
            .stFileUploader > div {
                background: linear-gradient(145deg, #1f2937, #111827) !important;
                border-color: #6366f1 !important;
                color: #f9fafb !important;
            }
            
            .stFileUploader > div:hover {
                background: linear-gradient(145deg, #374151, #1f2937) !important;
                border-color: #8b5cf6 !important;
            }
            
            .stTextInput > div > div > input {
                background: linear-gradient(145deg, #1f2937, #111827) !important;
                color: #f9fafb !important;
                border-color: #374151 !important;
            }
            
            .stTextInput > div > div > input:focus {
                border-color: #6366f1 !important;
                box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.2) !important;
            }
            
            .stRadio > div {
                background: linear-gradient(145deg, #1f2937, #111827) !important;
                border-color: #374151 !important;
                color: #f9fafb !important;
            }
            
            .stChatInput > div {
                background: linear-gradient(145deg, #1f2937, #111827) !important;
                border-color: #374151 !important;
            }
            
            .stChatInput input {
                color: #f9fafb !important;
            }
            
            .stChatInput input::placeholder {
                color: #9ca3af !important;
            }
            
            .streamlit-expanderHeader {
                background: linear-gradient(145deg, #1f2937, #111827) !important;
                color: #f9fafb !important;
                border-color: #374151 !important;
            }
            
            .streamlit-expanderHeader:hover {
                background: linear-gradient(145deg, #374151, #1f2937) !important;
                border-color: #6366f1 !important;
            }
            
            .streamlit-expanderContent {
                background: linear-gradient(145deg, #111827, #1f2937) !important;
                border-color: #374151 !important;
                color: #f9fafb !important;
            }
            
            .stCode {
                background: linear-gradient(145deg, #111827, #1f2937) !important;
                color: #f9fafb !important;
                border-color: #374151 !important;
            }
            
            /* Success/Info/Warning/Error messages - Dark theme contrast */
            .stSuccess {
                background: linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(5, 150, 105, 0.15)) !important;
                color: #10b981 !important;
                border-color: #10b981 !important;
            }
            
            .stInfo {
                background: linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(67, 56, 202, 0.15)) !important;
                color: #6366f1 !important;
                border-color: #6366f1 !important;
            }
            
            .stWarning {
                background: linear-gradient(135deg, rgba(245, 158, 11, 0.2), rgba(217, 119, 6, 0.15)) !important;
                color: #f59e0b !important;
                border-color: #f59e0b !important;
            }
            
            .stError {
                background: linear-gradient(135deg, rgba(239, 68, 68, 0.2), rgba(220, 38, 38, 0.15)) !important;
                color: #ef4444 !important;
                border-color: #ef4444 !important;
            }
        }
        
        /* Chat input with gradient styling - LIGHT THEME */
        .stChatInput > div {
            background: linear-gradient(145deg, #ffffff, #f8faff) !important;
            border: 2px solid #e8ecf7 !important;
            border-radius: 16px !important;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08) !important;
        }
        
        .stChatInput input {
            background: transparent !important;
            color: #1e293b !important;
            font-size: 1rem !important;
            font-family: 'Inter', sans-serif !important;
        }
        
        .stChatInput input::placeholder {
            color: #64748b !important;
        }
        
        /* File uploader with gradient styling - LIGHT THEME */
        .stFileUploader > div {
            background: linear-gradient(145deg, #f8faff, #ffffff) !important;
            border: 3px dashed #667eea !important;
            border-radius: 16px !important;
            padding: 3rem 2rem !important;
            text-align: center !important;
            transition: all 0.3s ease !important;
            position: relative !important;
            overflow: hidden !important;
            color: #1e293b !important;
        }
        
        .stFileUploader > div:hover {
            border-color: #764ba2 !important;
            background: linear-gradient(145deg, #f0f3ff, #f8faff) !important;
            transform: scale(1.02) !important;
        }
        
        /* Text input enhancement - LIGHT THEME */
        .stTextInput > div > div > input {
            border-radius: 12px;
            border: 2px solid #e8ecf7;
            padding: 0.75rem 1.25rem;
            font-size: 1rem;
            font-family: 'Inter', sans-serif;
            transition: all 0.3s ease;
            background: linear-gradient(145deg, #ffffff, #f8faff);
            color: #1e293b;
        }
        
        .stTextInput > div > div > input:focus {
            border-color: #667eea;
            box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1);
            background: #ffffff;
        }
        
        .stTextInput > div > div > input::placeholder {
            color: #64748b;
        }
        
        /* Radio button enhancement - LIGHT THEME */
        .stRadio > div {
            background: linear-gradient(145deg, #f8faff, #ffffff);
            border-radius: 12px;
            padding: 1rem;
            border: 1px solid #e8ecf7;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
            color: #1e293b;
        }
        
        /* Success/Info/Warning/Error messages with gradients - LIGHT THEME */
        .stSuccess {
            background: linear-gradient(135deg, rgba(16, 185, 129, 0.15), rgba(5, 150, 105, 0.1)) !important;
            color: #059669 !important;
            border: 1px solid #10b981 !important;
            border-radius: 12px !important;
            box-shadow: 0 4px 15px rgba(16, 185, 129, 0.1) !important;
            padding: 1rem !important;
        }
        
        .stInfo {
            background: linear-gradient(135deg, rgba(59, 130, 246, 0.15), rgba(29, 78, 216, 0.1)) !important;
            color: #2563eb !important;
            border: 1px solid #3b82f6 !important;
            border-radius: 12px !important;
            box-shadow: 0 4px 15px rgba(59, 130, 246, 0.1) !important;
            padding: 1rem !important;
        }
        
        .stWarning {
            background: linear-gradient(135deg, rgba(245, 158, 11, 0.15), rgba(217, 119, 6, 0.1)) !important;
            color: #d97706 !important;
            border: 1px solid #f59e0b !important;
            border-radius: 12px !important;
            box-shadow: 0 4px 15px rgba(245, 158, 11, 0.1) !important;
            padding: 1rem !important;
        }
        
        .stError {
            background: linear-gradient(135deg, rgba(239, 68, 68, 0.15), rgba(220, 38, 38, 0.1)) !important;
            color: #dc2626 !important;
            border: 1px solid #ef4444 !important;
            border-radius: 12px !important;
            box-shadow: 0 4px 15px rgba(239, 68, 68, 0.1) !important;
            padding: 1rem !important;
        }
        
        /* Expanders with gradient styling - LIGHT THEME */
        .streamlit-expanderHeader {
            background: linear-gradient(145deg, #f8faff, #ffffff) !important;
            color: #2c3e50 !important;
            border: 1px solid #e8ecf7 !important;
            border-radius: 12px !important;
            font-weight: 500 !important;
            font-family: 'Inter', sans-serif !important;
            transition: all 0.3s ease !important;
        }
        
        .streamlit-expanderHeader:hover {
            background: linear-gradient(145deg, #f0f3ff, #f8faff) !important;
            border-color: #667eea !important;
        }
        
        .streamlit-expanderContent {
            background: linear-gradient(145deg, #ffffff, #f8faff) !important;
            border: 1px solid #e8ecf7 !important;
            border-top: none !important;
            border-radius: 0 0 12px 12px !important;
            color: #1e293b !important;
        }
        
        /* Code blocks with enhanced styling - LIGHT THEME */
        .stCode {
            background: linear-gradient(145deg, #f1f5f9, #ffffff) !important;
            border: 1px solid #cbd5e1 !important;
            border-radius: 12px !important;
            color: #1e293b !important;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05) !important;
        }
        
        /* Responsive design */
        @media (max-width: 768px) {
            section[data-testid="stSidebar"] {
                width: 320px !important;
                min-width: 320px !important;
            }
            
            section[data-testid="stSidebar"] > div:first-child {
                width: 320px !important;
                min-width: 320px !important;
            }
            
            .main-header h1 {
                font-size: 2.2rem;
            }
            
            .main-header p {
                font-size: 1.1rem;
            }
        }
        
        /* Animation keyframes */
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .animated {
            animation: fadeInUp 0.6s ease-out;
        }
        
        /* Enhanced scrollbar - Theme adaptive */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: linear-gradient(145deg, #f1f5f9, #e2e8f0);
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb {
            background: linear-gradient(135deg, #667eea, #764ba2);
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: linear-gradient(135deg, #5a72e8, #6d42a0);
        }
        
        /* Dark theme scrollbar */
        @media (prefers-color-scheme: dark) {
            ::-webkit-scrollbar-track {
                background: linear-gradient(145deg, #1f2937, #111827);
                border-radius: 4px;
            }
            
            ::-webkit-scrollbar-thumb {
                background: linear-gradient(135deg, #4c1d95, #6366f1);
                border-radius: 4px;
            }
            
            ::-webkit-scrollbar-thumb:hover {
                background: linear-gradient(135deg, #3730a3, #4338ca);
            }
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Initialize session state and setup sidebar
    initialize_session_state()
    db_uri = setup_sidebar()
    
    # Enhanced title with current model display
    current_model = GROQ_MODELS[st.session_state.selected_model]
    
    st.markdown("""
    <div class="main-header animated">
        <h1>🤖 SQL Database Chat Agent</h1>
        <p>Transform natural language into powerful SQL queries with advanced AI</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Current model info
    st.markdown(f"""
    <div class="step-container animated">
        <strong>🧠 Currently using:</strong> {st.session_state.selected_model}<br>
        <small>{current_model['description']} • {current_model['speed']} • {current_model['cost']} • Context: {current_model['context']}</small>
    </div>
    """, unsafe_allow_html=True)
    
    if not st.session_state.db_connected:
        # Use proper streamlit info message instead of custom HTML
        st.info("👈 Please configure your database connection in the wider sidebar to start chatting.")
        
        # Use proper markdown without HTML tags for text content
        st.markdown(f"""
        ### 🚀 How to use this SQL Chat Agent:
        
        **1. Select AI Model:** Choose from {len(GROQ_MODELS)} different models in the sidebar (currently: **{st.session_state.selected_model}**)
        
        **2. Configure Database:** Upload a SQLite file or enter MySQL credentials in the sidebar
        
        **3. View Schema:** Check the database tables and columns in the sidebar
        
        **4. Try Examples:** Click example queries in the sidebar to execute them immediately
        
        **5. Ask Questions:** Use the chat input below to ask natural language questions
        
        **6. Get Answers:** The AI will generate SQL queries and provide detailed answers
        
        ### ✅ Perfect Chat Message Visibility:
        This app now features **high-contrast text in all chat messages** with dark text on light colored backgrounds in light theme, and light text on dark colored backgrounds in dark theme for perfect readability!
        """)
        return
    
    # Display chat history
    chat_container = st.container()
    
    with chat_container:
        for message in st.session_state.messages:
            display_chat_message(message)
    
    # Chat input at the bottom with model info
    if prompt := st.chat_input(f"Ask a question about your database... (using {st.session_state.selected_model})"):
        process_query(prompt)
        st.rerun()

if __name__ == "__main__":
    main()
