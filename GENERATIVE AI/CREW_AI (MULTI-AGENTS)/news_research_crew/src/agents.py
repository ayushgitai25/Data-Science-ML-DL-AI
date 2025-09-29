import os
from crewai import Agent
from .llm_config import LLMConfig
from .tools import get_available_tools

class NewsAgents:
    def __init__(self):
        # Get LLM (Google or Ollama)
        self.llm = LLMConfig.get_llm()
        
        # Both Google and Ollama work well with tools
        self.tools = get_available_tools()
        
        provider_info = LLMConfig.get_provider_info()
        print(f"📊 LLM: {provider_info.get('name', 'Unknown')}")
        print(f"🔧 Tools loaded: {len(self.tools)}")
    
    def news_researcher(self) -> Agent:
        return Agent(
            role="News Research Analyst", 
            goal="Research recent news using available search tools and provide comprehensive analysis",
            backstory="""You are a skilled researcher with access to multiple tools:

            1. **NewsData.io Search** - Search 84,000+ news sources for recent articles
            2. **Web Search** - Search the general web using DuckDuckGo (free)

            You excel at finding current information from both structured news sources and 
            general web content. Use news search for recent articles and web search for 
            broader information and different perspectives.""",
            tools=self.tools,
            llm=self.llm,
            verbose=True,
            max_iter=3,
            allow_delegation=False,
        )
    
    def content_writer(self) -> Agent:
        return Agent(
            role="Content Writer",
            goal="Create well-structured, engaging news reports with creative markdown formatting",
            backstory="""You are a skilled content writer who creates comprehensive, 
            newspaper-style reports with creative markdown formatting. You excel at making 
            complex information accessible and engaging through proper use of headers, 
            bullet points, tables, and visual elements.""",
            tools=[],  # Writer doesn't need tools
            llm=self.llm,
            verbose=True,
            max_iter=2,
            allow_delegation=False,
        )
