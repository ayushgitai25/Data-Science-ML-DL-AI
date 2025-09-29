import os
import requests
from typing import Type
from crewai.tools import BaseTool, tool
from pydantic import BaseModel, Field

# ===== CUSTOM NEWSDATA.IO TOOL =====
class NewsSearchInput(BaseModel):
    """Input schema for basic news search."""
    query: str = Field(..., description="Search query for news articles")
    max_results: int = Field(default=8, description="Maximum number of results to return (1-10)")

class BasicNewsSearchTool(BaseTool):
    name: str = "news_search"
    description: str = "Search for recent news articles on any topic using NewsData.io API"
    args_schema: Type[BaseModel] = NewsSearchInput

    def _run(self, query: str, max_results: int = 8) -> str:
        """Search for news articles using NewsData.io"""
        
        api_key = os.getenv('NEWSDATA_API_KEY')
        if not api_key:
            return "❌ NewsData API key not found"
        
        url = f"https://newsdata.io/api/1/news?apikey={api_key}&q={query}&size={min(max_results, 10)}"
        
        try:
            print(f"🔍 Searching news for: '{query}'")
            response = requests.get(url, timeout=20)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status') != 'success':
                return f"❌ API Error: {data.get('message', 'Unknown error')}"
            
            articles = data.get('results', [])
            
            if not articles:
                return f"No articles found for '{query}'"
            
            result = f"📰 Found {len(articles)} news articles for '{query}':\n\n"
            
            for i, article in enumerate(articles, 1):
                title = article.get('title', 'No title')
                source = article.get('source_name', article.get('source_id', 'Unknown'))
                date = article.get('pubDate', 'Unknown date')
                description = article.get('description', 'No description')
                
                result += f"**{i}. {title}**\n"
                result += f"   📰 Source: {source}\n" 
                result += f"   📅 Date: {date}\n"
                result += f"   📝 {description[:150]}...\n\n"
            
            return result
            
        except Exception as e:
            return f"❌ News search failed: {str(e)}"

# ===== FREE WEB SEARCH TOOL =====
# @tool("Web Search")
# def web_search(query: str) -> str:
#     """Search the web for information using DuckDuckGo (free, no API key needed)"""
    
#     try:
#         # Try to import and use DuckDuckGo
#         from duckduckgo_search import DDGS
        
#         print(f"🌐 Searching web for: '{query}'")
        
#         with DDGS() as ddgs:
#             results = list(ddgs.text(query, max_results=5))
        
#         if not results:
#             return f"No web results found for '{query}'"
        
#         output = f"🌐 Web search results for '{query}':\n\n"
        
#         for i, result in enumerate(results, 1):
#             title = result.get('title', 'No title')
#             url = result.get('href', 'No URL')
#             snippet = result.get('body', 'No description')
            
#             output += f"**{i}. {title}**\n"
#             output += f"   🔗 {url}\n"
#             output += f"   📝 {snippet[:150]}...\n\n"
        
#         return output
        
#     except ImportError:
#         return "❌ DuckDuckGo search not available. Install with: pip install duckduckgo-search"
#     except Exception as e:
#         return f"❌ Web search failed: {str(e)}"

# ===== TOOL COLLECTION FUNCTION =====
def get_available_tools():
    """Get list of available tools that work with CrewAI"""
    
    tools = []
    
    # Always add custom news search tool
    news_tool = BasicNewsSearchTool()
    tools.append(news_tool)
    print("✅ Added: NewsData.io Search Tool (custom)")
    
    # Add web search tool (using @tool decorator)
    # tools.append(web_search)
    # print("✅ Added: DuckDuckGo Web Search Tool (free)")
    
    print(f"🔧 Total tools available: {len(tools)}")
    return tools

# ===== TEST FUNCTION =====
def test_all_tools():
    """Test all available tools"""
    print("🧪 Testing Available Tools...")
    print("=" * 50)
    
    # Test 1: Custom news search
    print("1. Testing NewsData.io Tool:")
    news_tool = BasicNewsSearchTool()
    result = news_tool._run("artificial intelligence", 3)
    print(f"   Result: {result[:150]}...\n")
    
    # Test 2: Web search
    # print("2. Testing Web Search Tool:")
    # result = web_search("latest technology news")
    # print(f"   Result: {result[:150]}...\n")
    
    print("✅ All tools tested!")

if __name__ == "__main__":
    test_all_tools()
