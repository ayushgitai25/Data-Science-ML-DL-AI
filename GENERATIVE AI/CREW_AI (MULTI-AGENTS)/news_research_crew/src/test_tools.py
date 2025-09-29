import os
import sys
sys.path.append('src')
from dotenv import load_dotenv
from tools import test_all_tools, get_available_tools

load_dotenv()

if __name__ == "__main__":
    print("🧪 Testing All Available Tools")
    print("=" * 60)
    
    # Show available tools
    tools = get_available_tools()
    print(f"\n🔧 Available Tools: {len(tools)}")
    for i, tool in enumerate(tools, 1):
        tool_name = getattr(tool, 'name', str(type(tool).__name__))
        print(f"   {i}. {tool_name}")
    
    print("\n" + "=" * 60)
    test_all_tools()
