import os
from typing import Union
from dotenv import load_dotenv

load_dotenv()

class LLMConfig:
    """LLM configuration for Google Gemini and Ollama only"""
    
    @staticmethod
    def get_llm():
        """Get the configured LLM - Google or Ollama only"""
        provider = os.getenv('LLM_PROVIDER', 'google').lower()
        
        if provider == 'google':
            return LLMConfig._get_google_llm()
        elif provider == 'ollama':
            return LLMConfig._get_ollama_llm()
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}. Use 'google' or 'ollama'")
    
    @staticmethod
    def _get_google_llm():
        """Configure Google Gemini LLM"""
        try:
            from crewai import LLM
            
            api_key = os.getenv('GOOGLE_API_KEY')
            if not api_key:
                raise ValueError("GOOGLE_API_KEY not found in environment variables")
            
            print("🤖 Using Google Gemini 1.5 Flash")
            
            # Set environment variable for LiteLLM
            os.environ['GEMINI_API_KEY'] = api_key
            
            return LLM(
                model="gemini/gemini-2.5-flash",
                temperature=0.1,
                max_tokens=2048,
            )
            
        except ImportError:
            raise ImportError("CrewAI LLM class not available")
    
    @staticmethod
    def _get_ollama_llm():
        """Configure Ollama LLM"""
        try:
            from crewai import LLM
            
            model = os.getenv('OLLAMA_MODEL', 'gemma2:latest')
            
            print(f"🤖 Using Local Ollama {model}")
            return LLM(
                model=f"ollama/{model}",
                base_url="http://localhost:11434",
                temperature=0.1,
            )
            
        except ImportError:
            raise ImportError("CrewAI LLM class not available")
    
    @staticmethod
    def get_provider_info():
        """Get current LLM provider information"""
        provider = os.getenv('LLM_PROVIDER', 'google').lower()
        
        info = {
            'google': {
                'name': 'Google Gemini 2.5 Flash',
                'speed': 'Fast',
                'local': False
            },
            'ollama': {
                'name': f"Ollama {os.getenv('OLLAMA_MODEL', 'gemma2:latest')}",
                'cost': '100% Free',
                'speed': 'Depends on hardware',
                'local': True
            }
        }
        
        return info.get(provider, {})
