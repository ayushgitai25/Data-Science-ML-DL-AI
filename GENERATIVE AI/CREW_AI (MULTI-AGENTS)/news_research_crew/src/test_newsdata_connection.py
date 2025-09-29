import os
import requests
from dotenv import load_dotenv

load_dotenv()

def test_newsdata_connection():
    """Test NewsData.io connection"""
    api_key = os.getenv('NEWSDATA_API_KEY')
    if not api_key:
        print("❌ NEWSDATA_API_KEY not found")
        return False
    
    url = "https://newsdata.io/api/1/news"
    params = {'apikey': api_key, 'q': 'test', 'size': 1}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                print("✅ NewsData.io connection successful")
                print(f"📊 Credits remaining: {data.get('totalResults', 'Unknown')}")
                return True
            else:
                print(f"❌ API Error: {data.get('message', 'Unknown error')}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing NewsData.io Connection...")
    test_newsdata_connection()
