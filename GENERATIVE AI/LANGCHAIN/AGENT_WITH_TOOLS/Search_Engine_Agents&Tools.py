import streamlit as st
from langchain_community.tools import ArxivQueryRun, WikipediaQueryRun, DuckDuckGoSearchRun
from langchain_community.utilities import WikipediaAPIWrapper, ArxivAPIWrapper
from langchain_groq import ChatGroq
from langchain import hub
from langchain.agents import create_openai_tools_agent, AgentExecutor ## New Implementation
from langchain_community.callbacks.streamlit import StreamlitCallbackHandler
# ✅ Import message types for history
from langchain_core.messages import AIMessage, HumanMessage

import os
from dotenv import load_dotenv

# ------------------ ENVIRONMENT VARIABLES ------------------
load_dotenv()
os.environ['GROQ_API_KEY'] = os.getenv('GROQ_API_KEY')

# ------------------ DEFINE TOOLS ------------------
api_wrapper_wiki = WikipediaAPIWrapper(top_k_results=1, doc_content_chars_max=250)
wiki = WikipediaQueryRun(api_wrapper=api_wrapper_wiki)

api_wrapper_arxiv = ArxivAPIWrapper(top_k_results=1, doc_content_chars_max=250)
arxiv = ArxivQueryRun(api_wrapper=api_wrapper_arxiv)

duckDuckGoSearch = DuckDuckGoSearchRun(name="duckDuckGoSearch")

tools = [arxiv, wiki, duckDuckGoSearch]

# ------------------ LLM & AGENT ------------------
llm = ChatGroq(model="deepseek-r1-distill-llama-70b", streaming=True)

prompt = hub.pull("hwchase17/openai-functions-agent")

agent = create_openai_tools_agent(llm, tools, prompt)

agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    handle_parsing_errors=True,
    verbose=True
)

# ------------------ STREAMLIT UI ------------------
st.set_page_config(page_title="LangChain Multi-Tool Chat", page_icon="🤖", layout="centered")
st.title("🤖 LangChain Agent Chatbot with Tools")
st.markdown("Ask me anything, and I'll use Wikipedia, Arxiv and DuckDuckGoSearch")

# Initialize session history for UI display and agent memory
if "messages" not in st.session_state:
    st.session_state.messages = []
# ✅ Initialize history for the agent
if "history" not in st.session_state:
    st.session_state.history = []

# ------------------ CHAT HISTORY DISPLAY ------------------
# Show all previous messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ------------------ CHAT INPUT ------------------
if prompt_input := st.chat_input("Type your message..."):
    # --- USER MESSAGE ---
    st.session_state.messages.append({"role": "user", "content": prompt_input})
    with st.chat_message("user"):
        st.markdown(prompt_input)

    # --- ASSISTANT RESPONSE ---
    with st.chat_message("assistant"):
        container = st.container()
        
        with st.spinner("Thinking..."):
            callback = StreamlitCallbackHandler(container)
            
            try:
                # ✅ Pass the agent's chat history to the invoke method
                response = agent_executor.invoke(
                    {
                        "input": prompt_input,
                        "chat_history": st.session_state.history,
                    },
                    {"callbacks": [callback]}
                )
                answer = response.get("output", "Sorry, I couldn't find an answer.")
                
            except Exception as e:
                st.error(f"⚠️ Error: {str(e)}")
                answer = "Sorry, something went wrong."
        
        container.markdown(answer)

    # --- UPDATE HISTORY ---
    # Save assistant reply to UI history
    st.session_state.messages.append({"role": "assistant", "content": answer})
    # ✅ Save interaction to agent's history
    st.session_state.history.append(HumanMessage(content=prompt_input))
    st.session_state.history.append(AIMessage(content=answer))
