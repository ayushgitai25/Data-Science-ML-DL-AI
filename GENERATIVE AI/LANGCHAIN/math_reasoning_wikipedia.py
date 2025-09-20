import streamlit as st
import os
import math
import numexpr
from typing import Annotated, Sequence
from langchain_groq import ChatGroq
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate, MessagesPlaceholder
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_community.callbacks.streamlit import StreamlitCallbackHandler

# Page configuration
st.set_page_config(
    page_title="AI Agent Assistant",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .tool-card {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #667eea;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .example-card {
        background: #ffffff;
        padding: 1.2rem;
        border-radius: 8px;
        border: 1px solid #e9ecef;
        height: 100%;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    .status-success {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
    
    .status-warning {
        background: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
    
    .chat-input-container {
        background: #ffffff;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    
    .sidebar-section {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Main header
st.markdown("""
<div class="main-header">
    <h1>🚀 AI Agent Assistant</h1>
    <p>Your intelligent companion for calculations, research, and reasoning</p>
</div>
""", unsafe_allow_html=True)

# Sidebar configuration
with st.sidebar:
    st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.header("🔧 Configuration")
    st.markdown("</div>", unsafe_allow_html=True)
    
    with st.container():
        groq_api_key = st.text_input(
            "🔑 Groq API Key",
            type="password",
            help="Enter your Groq API key to enable the AI agent"
        )
        
        if groq_api_key:
            os.environ["GROQ_API_KEY"] = groq_api_key
            st.markdown('<div class="status-success">✅ API Key configured successfully!</div>', 
                       unsafe_allow_html=True)
        else:
            st.markdown('<div class="status-warning">⚠️ Please enter your API key to continue</div>', 
                       unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Model info
    st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.subheader("🤖 Model Information")
    st.info("**Model:** Gemma2-9b-It\n**Provider:** Groq\n**Temperature:** 0 (Deterministic)")
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Quick actions
    st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.subheader("⚡ Quick Actions")
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    
    if st.button("📊 Show Examples", use_container_width=True):
        st.session_state.show_examples = not getattr(st.session_state, 'show_examples', False)
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# Initialize components only if API key is provided
if groq_api_key:
    
    # Initialize ChatGroq with Gemma2-9b-It
    @st.cache_resource
    def initialize_llm():
        return ChatGroq(
            model_name="gemma2-9b-it",
            temperature=0,
            groq_api_key=groq_api_key,
            streaming=True
        )
    
    # Create Wikipedia wrapper tool
    @st.cache_resource
    def create_wikipedia_tool():
        wikipedia = WikipediaAPIWrapper(
            wiki_client=None,
            top_k_results=3,
            doc_content_chars_max=2000
        )
        return WikipediaQueryRun(api_wrapper=wikipedia)
    
    # Create calculator tool using numexpr (modern approach replacing math chain)
    @tool
    def calculator(expression: str) -> str:
        """Calculate mathematical expressions using Python's numexpr library.
        
        Expression should be a single line mathematical expression that solves the problem.
        
        Examples:
        "37593 * 67" for "37593 times 67"
        "37593**(1/5)" for "37593^(1/5)"
        "sqrt(16)" for "square root of 16"
        "pi * 2" for "pi times 2"
        """
        try:
            # Define local mathematical constants and functions
            local_dict = {
                "pi": math.pi, 
                "e": math.e,
                "sqrt": lambda x: x**0.5,
                "log": math.log,
                "sin": math.sin,
                "cos": math.cos,
                "tan": math.tan
            }
            
            # Evaluate the expression safely
            result = numexpr.evaluate(
                expression.strip(),
                global_dict={},  # Restrict access to globals for security
                local_dict=local_dict
            )
            return f"Result: {result}"
        except Exception as e:
            return f"Error in calculation: {str(e)}"
    
    # Create reasoning tool using the LLM chain
    @tool
    def reasoning_tool(question: str) -> str:
        """Use advanced reasoning to solve complex problems step by step.
        
        This tool leverages the LLM's reasoning capabilities for problems that require
        logical thinking, analysis, or step-by-step problem solving.
        """
        llm = initialize_llm()
        
        reasoning_prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template("""You are an expert reasoning assistant. Break down complex problems 
            into logical steps and provide clear, step-by-step explanations. Think carefully 
            about each step and explain your reasoning process."""),
            HumanMessagePromptTemplate.from_template("{question}")
        ])
        
        reasoning_chain = reasoning_prompt | llm
        response = reasoning_chain.invoke({"question": question})
        return response.content
    
    # Initialize tools
    try:
        llm = initialize_llm()
        wikipedia_tool = create_wikipedia_tool()
        
        # Combine all tools
        tools = [calculator, wikipedia_tool, reasoning_tool]
        
        # Tool overview section
        st.subheader("🛠️ Available Tools")
        tool_cols = st.columns(3)
        
        with tool_cols[0]:
            st.markdown("""
            <div class="tool-card">
                <h4>🧮 Calculator</h4>
                <p>Advanced mathematical calculations using numexpr</p>
                <small><strong>Supports:</strong> Basic math, trigonometry, constants</small>
            </div>
            """, unsafe_allow_html=True)
        
        with tool_cols[1]:
            st.markdown("""
            <div class="tool-card">
                <h4>📚 Wikipedia</h4>
                <p>Real-time information from Wikipedia</p>
                <small><strong>Features:</strong> Top 3 results, 2000 char limit</small>
            </div>
            """, unsafe_allow_html=True)
        
        with tool_cols[2]:
            st.markdown("""
            <div class="tool-card">
                <h4>🧠 Reasoning</h4>
                <p>Step-by-step logical problem solving</p>
                <small><strong>Capability:</strong> Complex analysis & reasoning</small>
            </div>
            """, unsafe_allow_html=True)
        
        # Create agent prompt template
        agent_prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template("""You are a helpful AI assistant with access to multiple tools:
1. **Calculator**: For mathematical calculations and expressions
2. **Wikipedia**: For searching factual information and knowledge
3. **Reasoning Tool**: For complex logical reasoning and step-by-step problem solving

Use these tools appropriately based on the user's question:
- Use the calculator for any mathematical operations
- Use Wikipedia to search for factual information about people, places, events, concepts
- Use the reasoning tool for complex analysis, logical problems, or multi-step reasoning

Always think step by step and use the most appropriate tool(s) for each question.
Be clear about which tool you're using and why."""),
            MessagesPlaceholder(variable_name="chat_history"),
            HumanMessagePromptTemplate.from_template("{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        # Create the agent
        agent = create_tool_calling_agent(llm, tools, agent_prompt)
        
        # Create agent executor
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=5
        )
        
        # Chat interface section
        st.markdown("---")
        st.subheader("💬 Chat Interface")
        
        # Initialize chat history
        if "messages" not in st.session_state:
            st.session_state.messages = []
        
        # Chat container with better styling
        chat_container = st.container()
        
        with chat_container:
            # Display chat history
            for i, message in enumerate(st.session_state.messages):
                if message["role"] == "user":
                    with st.chat_message("user", avatar="👤"):
                        st.markdown(f"**You:** {message['content']}")
                else:
                    with st.chat_message("assistant", avatar="🤖"):
                        st.markdown(message["content"])
        
        # Chat input with improved styling
        st.markdown('<div class="chat-input-container">', unsafe_allow_html=True)
        prompt = st.chat_input(
            "💭 Ask me anything! I can help with math, research, and complex reasoning...",
            key="main_chat_input"
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        if prompt:
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Display user message immediately
            with st.chat_message("user", avatar="👤"):
                st.markdown(f"**You:** {prompt}")
            
            # Generate and display assistant response
            with st.chat_message("assistant", avatar="🤖"):
                # Create container for streaming callback
                response_container = st.container()
                
                # Initialize StreamlitCallbackHandler
                st_callback = StreamlitCallbackHandler(
                    parent_container=response_container,
                    expand_new_thoughts=True,
                    collapse_completed_thoughts=True
                )
                
                try:
                    # Show loading spinner with custom message
                    with st.spinner("🤔 Processing your request..."):
                        response = agent_executor.invoke(
                            {
                                "input": prompt,
                                "chat_history": []  # You can implement chat history if needed
                            },
                            {"callbacks": [st_callback]}
                        )
                    
                    # Display final response
                    final_response = response.get("output", "I'm sorry, I couldn't process that request.")
                    st.markdown(final_response)
                    
                    # Add assistant response to chat history
                    st.session_state.messages.append({"role": "assistant", "content": final_response})
                    
                except Exception as e:
                    error_message = f"❌ An error occurred: {str(e)}"
                    st.error(error_message)
                    st.session_state.messages.append({"role": "assistant", "content": error_message})
        
        # Examples section (collapsible)
        if getattr(st.session_state, 'show_examples', True):
            st.markdown("---")
            st.subheader("💡 Example Queries")
            
            example_cols = st.columns(3)
            
            with example_cols[0]:
                st.markdown("""
                <div class="example-card">
                    <h4>🧮 Mathematics</h4>
                    <ul>
                        <li>What is 37593 × 67?</li>
                        <li>Calculate √144</li>
                        <li>What is π × 2.5?</li>
                        <li>Solve (15 + 25) × 3 ÷ 2</li>
                        <li>Find sin(π/2)</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
            
            with example_cols[1]:
                st.markdown("""
                <div class="example-card">
                    <h4>📚 Research</h4>
                    <ul>
                        <li>Tell me about Albert Einstein</li>
                        <li>What is machine learning?</li>
                        <li>History of Python programming</li>
                        <li>Artificial intelligence timeline</li>
                        <li>Quantum computing basics</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
            
            with example_cols[2]:
                st.markdown("""
                <div class="example-card">
                    <h4>🧠 Reasoning</h4>
                    <ul>
                        <li>Train traveling 60 mph for 2.5 hours?</li>
                        <li>Compare renewable vs fossil fuels</li>
                        <li>Explain photosynthesis steps</li>
                        <li>Climate change causes & effects</li>
                        <li>Problem-solving strategies</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
        
        # Stats section
        st.markdown("---")
        stats_cols = st.columns(4)
        
        with stats_cols[0]:
            st.metric("💬 Messages", len(st.session_state.messages))
        
        with stats_cols[1]:
            st.metric("🛠️ Tools", len(tools))
        
        with stats_cols[2]:
            st.metric("🤖 Model", "Gemma2-9b-It")
        
        with stats_cols[3]:
            st.metric("🌡️ Temperature", "0.0")
            
    except Exception as e:
        st.error(f"❌ Error initializing the application: {str(e)}")
        st.info("💡 Please make sure your Groq API key is valid and try again.")

else:
    # Welcome screen for users without API key
    st.markdown("---")
    
    welcome_cols = st.columns([1, 2, 1])
    with welcome_cols[1]:
        st.markdown("""
        <div style="text-align: center; padding: 2rem;">
            <h2>🚀 Welcome to AI Agent Assistant!</h2>
            <p style="font-size: 1.2em; color: #666;">
                Your intelligent companion for calculations, research, and reasoning
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # Getting started guide
    st.subheader("🏁 Getting Started")
    
    start_cols = st.columns(2)
    
    with start_cols[0]:
        st.markdown("""
        **📋 Setup Steps:**
        1. 🌐 Visit [Groq Console](https://console.groq.com/)
        2. 🔑 Create account & get API key
        3. 📝 Enter API key in sidebar
        4. 💬 Start chatting with the AI!
        """)
    
    with start_cols[1]:
        st.markdown("""
        **✨ Features:**
        - 🧮 Advanced mathematical calculations
        - 📚 Real-time Wikipedia research
        - 🧠 Complex reasoning & analysis
        - 💨 Streaming responses
        - 🎯 Multi-tool integration
        """)
    
    # Feature showcase
    st.subheader("🎯 What Can I Do?")
    
    feature_tabs = st.tabs(["🧮 Calculate", "📚 Research", "🧠 Reason"])
    
    with feature_tabs[0]:
        st.markdown("""
        **Mathematical Capabilities:**
        - Basic arithmetic operations
        - Advanced functions (trigonometry, logarithms)
        - Mathematical constants (π, e)
        - Complex expressions
        - Scientific calculations
        
        *Example: "Calculate the area of a circle with radius 5"*
        """)
    
    with feature_tabs[1]:
        st.markdown("""
        **Research Capabilities:**
        - Wikipedia knowledge base access
        - Real-time information retrieval
        - Multiple search results
        - Summarized content
        - Factual accuracy
        
        *Example: "Tell me about the latest developments in quantum computing"*
        """)
    
    with feature_tabs[2]:
        st.markdown("""
        **Reasoning Capabilities:**
        - Step-by-step problem solving
        - Logical analysis
        - Complex decision making
        - Multi-step processes
        - Critical thinking
        
        *Example: "Compare the pros and cons of different renewable energy sources"*
        """)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 2rem; color: #666;">
    <p><strong>Powered by:</strong> 
    <span style="color: #667eea;">LangChain</span> • 
    <span style="color: #667eea;">Streamlit</span> • 
    <span style="color: #667eea;">Groq Gemma2-9b-It</span>
    </p>
    <p><em>Built with ❤️ for intelligent conversations</em></p>
</div>
""", unsafe_allow_html=True)
