import os
import time
import sys
from datetime import datetime
from crewai import Crew, Process
from .agents import NewsAgents
from .tasks import NewsTasks
from .llm_config import LLMConfig

class NewsResearchCrew:
    """Main crew orchestrator for news research and content creation"""
    
    def __init__(self, topic: str, include_trending: bool = False):
        self.topic = topic
        self.include_trending = include_trending
        self.start_time = None
        self.agents_manager = NewsAgents()
        self.tasks_manager = NewsTasks()
        
        # Ensure outputs directory exists
        os.makedirs("outputs", exist_ok=True)
        
        # Get LLM provider info for logging
        self.llm_info = LLMConfig.get_provider_info()
        
        print(f"🤖 Initializing CrewAI with {self.llm_info.get('name', 'Unknown LLM')}")
        print(f"📰 Topic: {self.topic}")
        print(f"⚡ Speed: {self.llm_info.get('speed', 'Unknown')}")
        print(f"💰 Cost: {self.llm_info.get('cost', 'Unknown')}")
    
    def run(self):
        """Execute the complete news research crew workflow"""
        
        self.start_time = time.time()
        
        try:
            print(f"\n🚀 Starting news research crew for: '{self.topic}'")
            print("=" * 70)
            
            # Initialize agents
            print("👥 Initializing agents...")
            researcher = self.agents_manager.news_researcher()
            writer = self.agents_manager.content_writer()
            
            # Initialize tasks
            print("📋 Setting up tasks...")
            research_task = self.tasks_manager.research_news_task(researcher, self.topic)
            writing_task = self.tasks_manager.write_news_report_task(writer, self.topic)
            
            # Set task dependencies
            writing_task.context = [research_task]
            
            # Task list
            tasks = [research_task, writing_task]
            agents = [researcher, writer]
            
            # Create crew with correct boolean verbose
            crew = Crew(
                agents=agents,
                tasks=tasks,
                process=Process.sequential, ## Parallel if parallel execution is needed
                verbose=True,  # ✅ FIXED: Changed from verbose=2 to verbose=True
                max_rpm=15,  # Conservative rate limiting
            )
            
            # Execute the crew
            print(f"⚙️  Executing crew with {len(tasks)} tasks...")
            print("⏳ This may take 2-5 minutes depending on topic complexity...")
            print("-" * 70)
            
            result = crew.kickoff()
            
            # Process completion
            self._handle_completion(result)
            
            return result
            
        except KeyboardInterrupt:
            print("\n❌ Execution interrupted by user")
            self._cleanup()
            return None
            
        except Exception as e:
            print(f"\n❌ Error during crew execution: {str(e)}")
            
            # Handle specific error types
            if "rate" in str(e).lower() or "limit" in str(e).lower():
                print("🔄 Rate limit detected. Implementing retry logic...")
                return self._handle_rate_limit_retry()
            elif "api" in str(e).lower() or "key" in str(e).lower():
                print("🔑 API error detected. Check your API keys and try again.")
                return None
            elif "connection" in str(e).lower():
                print("🌐 Connection error. Check your internet connection.")
                return None
            else:
                print(f"🐛 Unexpected error: {str(e)}")
                raise e  # Re-raise for debugging
    
    def _handle_completion(self, result):
        """Handle successful crew completion"""
        end_time = time.time()
        duration = end_time - self.start_time
        
        print("\n" + "=" * 70)
        print("✅ NEWS RESEARCH CREW COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        
        # Execution summary
        print(f"⏱️  Execution time: {duration:.1f} seconds ({duration/60:.1f} minutes)")
        print(f"🤖 LLM used: {self.llm_info.get('name', 'Unknown')}")
        print(f"📰 Topic researched: {self.topic}")
        print(f"💰 Cost: {self.llm_info.get('cost', 'Unknown')}")
        
        # Output files
        print("\n📁 Generated files:")
        timestamp = self.tasks_manager.timestamp
        topic_clean = self.topic.replace(' ', '_').lower()
        
        files = [
            f"outputs/{topic_clean}_research_{timestamp}.md",
            f"outputs/{topic_clean}_final_report_{timestamp}.md"
        ]
        
        for file_path in files:
            if os.path.exists(file_path):
                size = os.path.getsize(file_path) / 1024  # KB
                print(f"   📄 {file_path} ({size:.1f} KB)")
            else:
                print(f"   ⚠️  {file_path} (not found)")
        
        print("\n💡 Tips:")
        print("   - Review the research file for source material")
        print("   - The final report is SEO-optimized and ready for publication")
        print("   - Check outputs/ directory for all generated files")
        
        # LLM-specific tips
        if self.llm_info.get('local'):
            print("   - Ollama results are completely private and local")
        else:
            print("   - Results processed using cloud LLM - review for sensitive content")
        
        print("=" * 70)
    
    def _handle_rate_limit_retry(self):
        """Handle rate limit errors with intelligent retry"""
        provider = os.getenv('LLM_PROVIDER', 'google').lower()
        
        if provider == 'groq':
            delay = 120  # 2 minutes for Groq
        elif provider == 'google':
            delay = 60   # 1 minute for Google
        else:
            delay = 30   # 30 seconds for others
        
        print(f"⏳ Waiting {delay} seconds before retry...")
        time.sleep(delay)
        
        print("🔄 Retrying crew execution...")
        return self.run()  # Retry once
    
    def _cleanup(self):
        """Cleanup resources on interruption"""
        if self.start_time:
            duration = time.time() - self.start_time
            print(f"\n🧹 Cleanup: Ran for {duration:.1f} seconds before interruption")
        
        # Check for partial outputs
        timestamp = self.tasks_manager.timestamp
        topic_clean = self.topic.replace(' ', '_').lower()
        research_file = f"outputs/{topic_clean}_research_{timestamp}.md"
        
        if os.path.exists(research_file):
            print(f"📄 Partial research saved: {research_file}")

# Utility function for quick crew execution
def run_news_crew(topic: str, include_trending: bool = False):
    """Quick utility function to run news crew"""
    crew = NewsResearchCrew(topic, include_trending)
    return crew.run()
