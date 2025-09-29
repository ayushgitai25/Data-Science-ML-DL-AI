from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os
import uvicorn
from typing import Optional
import json
from datetime import datetime
from dotenv import load_dotenv

# ✅ CRITICAL: Force reload environment variables
load_dotenv(override=True)

# Import our API components
from api.models import NewsRequest, NewsResponse, StatusResponse, ConfigResponse
from api.routes import router
from api.background_tasks import JobManager

# Initialize FastAPI app
app = FastAPI(
    title="CrewAI News Research API",
    description="AI-powered news research using CrewAI with Google Gemini & Ollama",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# ✅ Add CORS middleware with proper settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
os.makedirs("outputs", exist_ok=True)
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize job manager
job_manager = JobManager()

# Include API routes
app.include_router(router, prefix="/api/v1")

@app.get("/", response_class=HTMLResponse)
async def root():
    """Landing page with API documentation"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>CrewAI News Research API</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }
            .header { text-align: center; color: #333; }
            .endpoint { background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #007bff; }
            .method { color: #007bff; font-weight: bold; }
            .status { padding: 5px 10px; border-radius: 15px; color: white; font-size: 12px; }
            .active { background: #28a745; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🤖 CrewAI News Research API</h1>
                <p>AI-powered news research using Google Gemini & Ollama</p>
                <span class="status active">ACTIVE</span>
            </div>
            
            <h2>📚 API Documentation</h2>
            <div class="endpoint">
                <span class="method">GET</span> <code>/docs</code> - Interactive API documentation (Swagger UI)
            </div>
            <div class="endpoint">
                <span class="method">GET</span> <code>/health</code> - Health check endpoint
            </div>
            
            <h2>🔧 Main Endpoints</h2>
            <div class="endpoint">
                <span class="method">POST</span> <code>/api/v1/research</code> - Start news research job
            </div>
            <div class="endpoint">
                <span class="method">GET</span> <code>/api/v1/status/{job_id}</code> - Check job status
            </div>
            <div class="endpoint">
                <span class="method">GET</span> <code>/api/v1/results/{job_id}</code> - Get research results
            </div>
            
            <p style="text-align: center; margin-top: 30px; color: #666;">
                Built with ❤️ using CrewAI, FastAPI, and modern AI tools
            </p>
        </div>
    </body>
    </html>
    """

@app.get("/health")
async def health_check():
    """Fast health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "backend": "FastAPI",
        "services": {
            "newsdata_api": bool(os.getenv('NEWSDATA_API_KEY')),
            "google_gemini": bool(os.getenv('GOOGLE_API_KEY')),
            "llm_provider": os.getenv('LLM_PROVIDER', 'google')
        }
    }

# ✅ Add startup event for configuration verification
@app.on_event("startup")
async def startup_event():
    """Verify configuration on startup"""
    print("\n🚀 FastAPI Startup - Configuration Check:")
    print("=" * 50)
    
    # Test environment variables
    google_key = os.getenv('GOOGLE_API_KEY')
    if google_key:
        print(f"✅ Google API Key: {google_key[:10]}...{google_key[-4:]} (masked)")
    else:
        print("❌ Google API Key: Missing")
    
    newsdata_key = os.getenv('NEWSDATA_API_KEY')
    if newsdata_key:
        print(f"✅ NewsData API Key: {newsdata_key[:10]}...{newsdata_key[-4:]} (masked)")
    else:
        print("❌ NewsData API Key: Missing")
    
    print(f"✅ LLM Provider: {os.getenv('LLM_PROVIDER', 'google')}")
    print("🎉 FastAPI startup complete!")
    print("🌐 Access points:")
    print("   - API: http://localhost:8000")
    print("   - Docs: http://localhost:8000/docs")
    print("   - Health: http://localhost:8000/health")
    print("=" * 50)

if __name__ == "__main__":
    # Development server with optimized settings
    uvicorn.run(
        "app:app",
        host="0.0.0.0",  # ✅ Bind to all interfaces
        port=8000,
        reload=True,
        log_level="info",
        reload_delay=0.25,  # Faster reload
        workers=1  # Single worker for development
    )