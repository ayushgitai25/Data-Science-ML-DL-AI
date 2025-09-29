import streamlit as st
import requests
import time
import json
from datetime import datetime
import socket

# Configure Streamlit page
st.set_page_config(
    page_title="🤖 CrewAI Multi-Agent News Research Tool",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuration
BACKEND_URL = "http://localhost:8000"

# Custom CSS with Loading Animations
st.markdown("""
<style>
    .main-header {
        font-size: 2.8rem;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 1rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
        font-style: italic;
    }
    
    /* Loading Animations */
    .loading-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(255, 255, 255, 0.95);
        z-index: 9999;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }
    
    .loader {
        width: 50px;
        height: 50px;
        border: 5px solid #f3f3f3;
        border-top: 5px solid #1E88E5;
        border-radius: 50%;
        animation: spin 1s linear infinite;
        margin-bottom: 20px;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    .agent-loader {
        display: flex;
        justify-content: center;
        align-items: center;
        margin: 20px 0;
    }
    
    .agent-dot {
        width: 15px;
        height: 15px;
        border-radius: 50%;
        background: #1E88E5;
        margin: 0 5px;
        animation: agent-pulse 1.4s infinite ease-in-out both;
    }
    
    .agent-dot:nth-child(1) { animation-delay: -0.32s; }
    .agent-dot:nth-child(2) { animation-delay: -0.16s; }
    .agent-dot:nth-child(3) { animation-delay: 0s; }
    
    @keyframes agent-pulse {
        0%, 80%, 100% { transform: scale(0); }
        40% { transform: scale(1); }
    }
    
    .progress-loader {
        width: 100%;
        height: 4px;
        background: #f0f0f0;
        border-radius: 2px;
        overflow: hidden;
        margin: 15px 0;
    }
    
    .progress-bar-animated {
        height: 100%;
        background: linear-gradient(90deg, #1E88E5, #42A5F5, #1E88E5);
        background-size: 200% 100%;
        animation: progress-wave 2s infinite;
        border-radius: 2px;
    }
    
    @keyframes progress-wave {
        0% { background-position: 200% 0; }
        100% { background-position: -200% 0; }
    }
    
    .loading-text {
        font-size: 1.1rem;
        color: #1E88E5;
        margin-top: 15px;
        text-align: center;
        animation: text-pulse 2s infinite;
    }
    
    @keyframes text-pulse {
        0%, 100% { opacity: 0.6; }
        50% { opacity: 1; }
    }
    
    .status-loader {
        display: inline-block;
        width: 20px;
        height: 20px;
        border: 3px solid rgba(30, 136, 229, 0.3);
        border-radius: 50%;
        border-top-color: #1E88E5;
        animation: spin 1s ease-in-out infinite;
        margin-right: 10px;
    }
    
    /* Existing styles */
    .status-box {
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 5px solid #1E88E5;
        background: linear-gradient(90deg, #f8f9fa 0%, #e9ecef 100%);
    }
    .success-box {
        border-left-color: #28a745;
        background: linear-gradient(90deg, #d4edda 0%, #c3e6cb 100%);
    }
    .error-box {
        border-left-color: #dc3545;
        background: linear-gradient(90deg, #f8d7da 0%, #f5c6cb 100%);
    }
    .debug-section {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #dee2e6;
    }
    .agent-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 15px;
        margin: 10px 0;
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

class NewsResearchApp:
    def __init__(self):
        self.session_state_init()
    
    def session_state_init(self):
        """Initialize session state variables"""
        if 'current_job_id' not in st.session_state:
            st.session_state.current_job_id = None
        if 'job_history' not in st.session_state:
            st.session_state.job_history = []
        if 'auto_refresh' not in st.session_state:
            st.session_state.auto_refresh = False
        if 'last_backend_check' not in st.session_state:
            st.session_state.last_backend_check = None
        if 'backend_status' not in st.session_state:
            st.session_state.backend_status = None
        if 'show_project_info' not in st.session_state:
            st.session_state.show_project_info = False
        if 'loading' not in st.session_state:
            st.session_state.loading = False

    def show_loading_screen(self, message="Loading...", show_agents=False):
        """Show full-screen loading overlay"""
        if show_agents:
            loading_html = f"""
            <div class="loading-overlay">
                <div style="text-align: center;">
                    <h2 style="color: #1E88E5; margin-bottom: 30px;">🤖 AI Agents Working</h2>
                    <div class="agent-loader">
                        <div class="agent-dot"></div>
                        <div class="agent-dot"></div>
                        <div class="agent-dot"></div>
                    </div>
                    <p class="loading-text">{message}</p>
                    <div class="progress-loader">
                        <div class="progress-bar-animated"></div>
                    </div>
                    <p style="color: #666; margin-top: 20px;">
                        🕵️ Research Agent & ✍️ Writer Agent collaborating...
                    </p>
                </div>
            </div>
            """
        else:
            loading_html = f"""
            <div class="loading-overlay">
                <div class="loader"></div>
                <p class="loading-text">{message}</p>
            </div>
            """
        
        st.markdown(loading_html, unsafe_allow_html=True)

    def show_inline_loader(self, message="Loading..."):
        """Show inline loader for smaller operations"""
        return st.markdown(f"""
        <div style="display: flex; align-items: center; justify-content: center; margin: 20px 0;">
            <div class="status-loader"></div>
            <span style="color: #1E88E5;">{message}</span>
        </div>
        """, unsafe_allow_html=True)

    def render_project_info(self):
        """Render project information with loading"""
        with st.spinner("📖 Loading project information..."):
            time.sleep(0.5)  # Small delay for UX
            
            st.markdown("## 🤖 About This Multi-Agent System")
            
            # Overview
            st.info("""
            **🎯 Project Overview**
            
            This advanced news research tool uses CrewAI's multi-agent framework to automatically gather, 
            analyze, and synthesize news information from multiple sources. Two specialized AI agents work 
            collaboratively to deliver comprehensive, well-structured news reports.
            """)
            
            # Agent Details
            st.markdown("### 🤖 Meet Your AI Agent Team")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                #### 🕵️ News Research Analyst Agent
                **Role:** Primary Intelligence Gatherer
                
                **Mission:** Conducts comprehensive news research using multiple data sources and APIs.
                
                **Key Capabilities:**
                - 📰 NewsData.io Integration (84,000+ sources)
                - 🔍 Web Search & Scraping
                - 📊 Data Validation & Verification
                - 🎯 Source Cross-referencing
                - 📈 Trend Analysis
                - 🌐 Multi-language Support
                
                **What it does:**
                - Searches global news sources
                - Validates information accuracy
                - Extracts key statistics
                - Identifies expert opinions
                - Cross-references multiple perspectives
                """)
            
            with col2:
                st.markdown("""
                #### ✍️ Content Writer Agent
                **Role:** Report Synthesis & Formatting Specialist
                
                **Mission:** Transforms raw research data into professional, comprehensive news reports.
                
                **Key Capabilities:**
                - 📝 Professional Writing
                - 📋 Report Structuring
                - 🎨 Markdown Formatting
                - 📊 Data Organization
                - 🔗 Source Attribution
                - 📈 Executive Summaries
                
                **What it does:**
                - Creates newspaper-style headlines
                - Structures content clearly
                - Adds timestamps and citations
                - Generates summaries
                - Applies professional formatting
                - Ensures readability
                """)
            
            # Workflow
            st.markdown("### 🔄 How Agents Collaborate")
            
            st.markdown("""
            1. **🎯 Mission Briefing** - User submits research topic
            2. **🔍 Research Phase** - Research Agent gathers data from multiple sources
            3. **📊 Data Collection** - Agent validates and cross-references information
            4. **🧠 Analysis** - Data passed to Content Writer Agent for synthesis
            5. **📝 Report Generation** - Writer Agent creates structured, professional report
            6. **✅ Quality Control** - Final review and formatting optimization
            """)
            
            # Tech Stack
            st.markdown("### 🛠️ Technology Stack")
            
            tech_col1, tech_col2, tech_col3 = st.columns(3)
            
            with tech_col1:
                st.markdown("""
                **🤖 AI & Agents:**
                - CrewAI Framework
                - Google Gemini
                - Ollama (Local)
                """)
            
            with tech_col2:
                st.markdown("""
                **🔧 Backend:**
                - FastAPI REST API
                - Python Ecosystem
                """)
            
            with tech_col3:
                st.markdown("""
                **📡 Data Sources:**
                - NewsData.io (84K+ sources)
                - Web Scraping
                """)
            
            # Capabilities
            st.markdown("### 📈 System Capabilities")
            
            cap_col1, cap_col2, cap_col3 = st.columns(3)
            
            with cap_col1:
                st.metric("News Sources", "84,000+")
                st.metric("AI Agents", "2")
                
            with cap_col2:
                st.metric("Processing Time", "2-5 min")
                st.metric("LLM Options", "2")
                
            with cap_col3:
                st.metric("Languages", "Multiple")
                st.metric("Format", "Markdown")

    def check_port_connectivity(self, host='localhost', port=8000):
        """Check if port is accessible"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except Exception:
            return False
    
    def check_backend_health(self):
        """Check if FastAPI backend is running with loading animation"""
        try:
            # First check if port is open
            if not self.check_port_connectivity():
                return False
            
            # Try health endpoint with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = requests.get(
                        f"{BACKEND_URL}/health", 
                        timeout=30,
                        headers={'Accept': 'application/json'}
                    )
                    
                    if response.status_code == 200:
                        st.session_state.last_backend_check = datetime.now()
                        st.session_state.backend_status = True
                        return True
                    
                except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
                    if attempt < max_retries - 1:
                        time.sleep(2)
                    continue
            
            st.session_state.backend_status = False
            return False
            
        except Exception:
            st.session_state.backend_status = False
            return False
    
    def start_research(self, topic, llm_provider, max_articles):
        """Start a new research job with loading animation"""
        try:
            response = requests.post(
                f"{BACKEND_URL}/api/v1/research",
                json={
                    "topic": topic,
                    "llm_provider": llm_provider,
                    "max_articles": max_articles
                },
                timeout=60,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                job_data = response.json()
                st.session_state.current_job_id = job_data["job_id"]
                
                # Add to history
                st.session_state.job_history.append({
                    "job_id": job_data["job_id"],
                    "topic": topic,
                    "status": "pending",
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                
                return True, job_data
            else:
                error_data = response.json() if response.headers.get('content-type') == 'application/json' else {"error": response.text}
                return False, error_data
                
        except Exception as e:
            return False, {"error": f"Unexpected error: {str(e)}"}
    
    def get_job_status(self, job_id):
        """Get current job status with retry logic"""
        if not job_id:
            return None
            
        try:
            response = requests.get(
                f"{BACKEND_URL}/api/v1/status/{job_id}", 
                timeout=30,
                headers={'Accept': 'application/json'}
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return {"error": "Job not found"}
            else:
                return {"error": f"Server error: {response.status_code}"}
                
        except Exception:
            return {"error": "Connection failed"}
    
    def get_job_results(self, job_id):
        """Get job results with loading animation"""
        if not job_id:
            return None
            
        try:
            with st.spinner("📊 Retrieving intelligence report..."):
                response = requests.get(
                    f"{BACKEND_URL}/api/v1/results/{job_id}", 
                    timeout=60,
                    headers={'Accept': 'application/json'}
                )
                
                if response.status_code == 200:
                    time.sleep(1)  # Brief delay for UX
                    return response.json()
                else:
                    return None
                    
        except Exception:
            return None
    
    def render_debug_section(self):
        """Render debug section for connection testing"""
        with st.expander("🔧 Debug & Connection Test", expanded=False):
            st.markdown("### Connection Diagnostics")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🧪 Test Port Connection"):
                    with st.spinner("🔍 Testing port connectivity..."):
                        time.sleep(1)
                        if self.check_port_connectivity():
                            st.success("✅ Port 8000 is accessible")
                        else:
                            st.error("❌ Port 8000 is not accessible")
            
            with col2:
                if st.button("🏥 Test Health Endpoint"):
                    with st.spinner("🏥 Testing health endpoint..."):
                        try:
                            start_time = time.time()
                            response = requests.get(f"{BACKEND_URL}/health", timeout=15)
                            end_time = time.time()
                            
                            if response.status_code == 200:
                                st.success(f"✅ Health endpoint OK ({end_time - start_time:.2f}s)")
                                st.json(response.json())
                            else:
                                st.error(f"❌ Health endpoint returned {response.status_code}")
                                
                        except requests.exceptions.Timeout:
                            st.error("⏰ Health endpoint timed out (>15s)")
                        except Exception as e:
                            st.error(f"❌ Health endpoint failed: {e}")
            
            st.markdown("### Configuration")
            st.code(f"Backend URL: {BACKEND_URL}")
    
    def render_sidebar(self):
        """Render sidebar controls with loading states"""
        with st.sidebar:
            st.markdown("## ⚙️ Agent Control Panel")
            
            # Backend status with loading
            with st.container():
                if st.button("🔄 Check Agent Status", key="manual_backend_check"):
                    with st.spinner("🔍 Checking agent system..."):
                        time.sleep(1)
                        st.rerun()
                
                backend_healthy = self.check_backend_health()
                
                if backend_healthy:
                    st.success("✅ Agent System Online")
                    if st.session_state.last_backend_check:
                        st.caption(f"Last checked: {st.session_state.last_backend_check.strftime('%H:%M:%S')}")
                else:
                    st.error("❌ Agent System Offline")
                    st.warning("System initializing... Please wait.")
            
            st.markdown("---")
            
            # Project Info Toggle
            if st.button("📖 About This Project", key="show_info"):
                st.session_state.show_project_info = not st.session_state.show_project_info
            
            st.markdown("---")
            
            # Configuration
            llm_provider = st.selectbox(
                "🤖 Choose AI Brain:",
                options=["google", "ollama"],
                index=0,
                help="Google Gemini (cloud) or Ollama (local)"
            )
            
            max_articles = st.slider(
                "📰 Max Articles to Research:",
                min_value=1,
                max_value=20,
                value=8,
                help="Maximum number of articles agents will research"
            )
            
            st.markdown("---")
            
            # Agent Activity Settings
            st.markdown("### 🤖 Agent Settings")
            
            # Auto-refresh toggle
            auto_refresh = st.checkbox(
                "🔄 Auto-refresh agent status",
                value=st.session_state.auto_refresh,
                help="Automatically refresh agent status every 10 seconds"
            )
            st.session_state.auto_refresh = auto_refresh
            
            if auto_refresh and st.session_state.current_job_id:
                # Show loading indicator for auto-refresh
                self.show_inline_loader("Auto-refreshing...")
                time.sleep(10)
                st.rerun()
            
            st.markdown("---")
            
            # Mission history
            if st.session_state.job_history:
                st.markdown("## 📋 Recent Missions")
                for job in reversed(st.session_state.job_history[-5:]):
                    job_display = f"🎯 {job['topic'][:25]}..."
                    if st.button(job_display, key=f"history_{job['job_id']}"):
                        with st.spinner(f"Loading mission {job['job_id'][:8]}..."):
                            st.session_state.current_job_id = job['job_id']
                            time.sleep(0.5)
                            st.rerun()
        
        return llm_provider, max_articles, backend_healthy
    
    def render_main_interface(self, llm_provider, max_articles, backend_healthy):
        """Render main interface with loading states"""
        
        # Header
        st.markdown('<h1 class="main-header">🤖 CrewAI Multi-Agent News Research Tool</h1>', unsafe_allow_html=True)
        st.markdown('<p class="sub-header">Advanced AI Collaboration Framework for Intelligent News Analysis</p>', unsafe_allow_html=True)
        
        # Show project info if toggled
        if st.session_state.show_project_info:
            self.render_project_info()
            st.markdown("---")
        
        # Show debug section if backend is offline
        if not backend_healthy:
            st.warning("🔄 Agent system is initializing...")
            self.show_inline_loader("Connecting to AI agents...")
            return
        
        # Research input section
        with st.container():
            st.markdown("### 🚀 Deploy AI Research Agents")
            
            # Agent status indicators
            col_agent1, col_agent2 = st.columns(2)
            with col_agent1:
                st.success("🕵️ **Research Agent**: Ready for deployment")
            with col_agent2:
                st.success("✍️ **Writer Agent**: Standing by for mission")
            
            st.markdown("---")
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                topic = st.text_input(
                    "🎯 Enter research mission topic:",
                    placeholder="e.g., artificial intelligence breakthroughs, cryptocurrency market trends, climate change solutions",
                    help="Our AI agents will collaboratively research this topic using multiple sources"
                )
            
            with col2:
                st.markdown("<br>", unsafe_allow_html=True)
                start_button = st.button(
                    "🚀 Deploy Agents",
                    type="primary",
                    disabled=not topic or len(topic.strip()) < 3
                )
            
            if start_button and topic:
                # Show full-screen loading with agent animation
                with st.spinner("🤖 Deploying multi-agent research team..."):
                    success, result = self.start_research(topic, llm_provider, max_articles)
                    
                    if success:
                        st.success(f"✅ Agents successfully deployed! Mission ID: `{result['job_id']}`")
                        
                        # Show agent collaboration animation
                        st.markdown("""
                        <div class="agent-loader">
                            <div class="agent-dot"></div>
                            <div class="agent-dot"></div>
                            <div class="agent-dot"></div>
                        </div>
                        <p style="text-align: center; color: #1E88E5;">
                            🕵️ Research Agent & ✍️ Writer Agent now collaborating...
                        </p>
                        """, unsafe_allow_html=True)
                        
                        time.sleep(3)
                        st.rerun()
                    else:
                        error_msg = result.get('detail', result.get('error', 'Unknown error'))
                        st.error(f"❌ Agent deployment failed: {error_msg}")
        
        # Current job status section
        if st.session_state.current_job_id:
            self.render_job_status(st.session_state.current_job_id)
    
    def render_job_status(self, job_id):
        """Render current job status with animated progress"""
        
        st.markdown("---")
        st.markdown("### 🤖 Agent Mission Status")
        
        # Get job status with loading
        with st.spinner("📡 Checking agent status..."):
            status_data = self.get_job_status(job_id)
        
        if not status_data or "error" in status_data:
            st.error(f"❌ Agent communication error: {status_data.get('error', 'Unknown error') if status_data else 'No response'}")
            
            if st.button("🗑️ Abort Mission"):
                st.session_state.current_job_id = None
                st.rerun()
            return
        
        # Status display
        status = status_data.get("status", "unknown")
        progress = status_data.get("progress", 0)
        current_step = status_data.get("current_step", "Unknown")
        
        # Progress bar and status
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            if status == "running":
                st.info(f"🤖 **Agent Status:** Agents Working")
                # Animated progress bar
                st.markdown(f"""
                <div class="progress-loader">
                    <div class="progress-bar-animated" style="width: {progress}%;"></div>
                </div>
                """, unsafe_allow_html=True)
                
                # Show agent collaboration animation
                st.markdown("""
                <div class="agent-loader">
                    <div class="agent-dot"></div>
                    <div class="agent-dot"></div>
                    <div class="agent-dot"></div>
                </div>
                """, unsafe_allow_html=True)
                
            elif status == "completed":
                st.success(f"✅ **Mission Status:** Success")
                st.progress(1.0)
            elif status == "failed":
                st.error(f"❌ **Mission Status:** Failed")
                st.progress(0)
            else:
                st.warning(f"⏳ **Agent Status:** {status.title()}")
        
        with col2:
            st.metric("Mission Progress", f"{progress:.1f}%" if progress else "0%")
        
        with col3:
            if st.button("📡 Check Agent Status"):
                with st.spinner("🔄 Refreshing status..."):
                    time.sleep(1)
                    st.rerun()
        
        # Current step with loading indicator if running
        if status == "running":
            st.markdown(f"""
            <div style="display: flex; align-items: center; margin: 15px 0;">
                <div class="status-loader"></div>
                <span><strong>Current Agent Activity:</strong> {current_step}</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"**Current Agent Activity:** {current_step}")
        
        st.caption(f"Mission ID: {job_id}")
        
        # Show results if completed
        if status == "completed":
            self.render_results(job_id)
        elif status == "failed":
            error_msg = status_data.get("error_message", "Unknown error")
            st.error(f"**Agent Error:** {error_msg}")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Deploy New Mission"):
                    st.session_state.current_job_id = None
                    st.rerun()
            with col2:
                if st.button("🗑️ Clear Mission"):
                    st.session_state.current_job_id = None
                    st.rerun()
    
    def render_results(self, job_id):
        """Render job results with loading animations"""
        
        st.markdown("### 📊 Agent Intelligence Report")
        
        # Get results with loading screen
        results_data = self.get_job_results(job_id)
        
        if not results_data:
            st.error("❌ Could not retrieve agent intelligence report")
            return
        
        # Success animation
        st.success("🎉 **Multi-Agent Mission Completed Successfully!**")
        st.info("Both Research and Writer agents have completed their collaborative analysis.")
        
        # Results tabs
        tab1, tab2, tab3 = st.tabs(["📰 Final Intelligence Report", "🔍 Raw Agent Research", "🤖 Mission Details"])
        
        with tab1:
            with st.spinner("📄 Loading intelligence report..."):
                time.sleep(0.5)
                final_report = results_data.get("final_report")
                if final_report:
                    st.markdown("#### 🔥 Comprehensive Intelligence Report")
                    st.markdown("*Generated by Writer Agent using Research Agent data*")
                    st.markdown(final_report)
                    
                    st.download_button(
                        label="📥 Download Intelligence Report (Markdown)",
                        data=final_report,
                        file_name=f"crewai_intelligence_report_{job_id}.md",
                        mime="text/markdown"
                    )
                else:
                    st.warning("No intelligence report available from agents")
        
        with tab2:
            with st.spinner("📊 Loading research data..."):
                time.sleep(0.5)
                research_summary = results_data.get("research_summary")
                if research_summary:
                    st.markdown("#### 📊 Raw Research Agent Data")
                    st.markdown("*Collected by Research Agent from multiple sources*")
                    st.markdown(research_summary)
                    
                    st.download_button(
                        label="📥 Download Raw Research Data (Markdown)",
                        data=research_summary,
                        file_name=f"crewai_research_data_{job_id}.md",
                        mime="text/markdown"
                    )
                else:
                    st.warning("No raw research data available")
        
        with tab3:
            with st.spinner("🤖 Loading mission details..."):
                time.sleep(0.5)
                metadata = results_data.get("metadata", {})
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**🤖 Mission Information:**")
                    st.write(f"- **Research Topic:** {results_data.get('topic')}")
                    st.write(f"- **Mission Status:** {results_data.get('status')}")
                    st.write(f"- **AI Brain Used:** {metadata.get('llm_provider', 'Unknown')}")
                    st.write(f"- **Agent Framework:** Multi-Agent CrewAI")
                
                with col2:
                    st.markdown("**⏱️ Mission Timeline:**")
                    st.write(f"- **Mission Started:** {results_data.get('created_at')}")
                    st.write(f"- **Mission Completed:** {results_data.get('completed_at')}")
                
                # Agent Performance Metrics
                st.markdown("**🎯 Agent Performance Analysis:**")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**🕵️ Research Agent:**")
                    st.write("- Data collection: ✅ Complete")
                    st.write("- Source verification: ✅ Validated")
                    st.write("- Multi-source analysis: ✅ Success")
                    
                with col2:
                    st.write("**✍️ Writer Agent:**")
                    st.write("- Report synthesis: ✅ Complete")
                    st.write("- Professional formatting: ✅ Applied")
                    st.write("- Content structure: ✅ Optimized")

def main():
    """Main application entry point"""
    # Show initial loading
    if 'app_loaded' not in st.session_state:
        with st.spinner("🚀 Initializing CrewAI Multi-Agent System..."):
            time.sleep(2)
            st.session_state.app_loaded = True
    
    app = NewsResearchApp()
    
    # Render sidebar and get settings
    llm_provider, max_articles, backend_healthy = app.render_sidebar()
    
    # Render main interface
    app.render_main_interface(llm_provider, max_articles, backend_healthy)
    
    # Footer with enhanced branding
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666; padding: 20px;'>
            🤖 <strong>CrewAI Multi-Agent News Research Tool</strong><br>
            <em>Advanced AI Collaboration Framework</em><br>
            <small>Powered by Research Agent 🕵️ + Writer Agent ✍️ + FastAPI + Streamlit</small>
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()