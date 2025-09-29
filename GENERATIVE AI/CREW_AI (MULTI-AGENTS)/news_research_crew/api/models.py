from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

class LLMProvider(str, Enum):
    google = "google"
    ollama = "ollama"

class JobStatus(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"

class NewsRequest(BaseModel):
    topic: str = Field(..., description="News topic to research", min_length=1, max_length=200)
    llm_provider: Optional[LLMProvider] = Field(default=LLMProvider.google, description="LLM provider to use")
    max_articles: Optional[int] = Field(default=8, description="Maximum number of articles to fetch", ge=1, le=20)
    
    class Config:
        # ✅ FIXED: Updated for Pydantic V2
        json_schema_extra = {
            "example": {
                "topic": "artificial intelligence developments",
                "llm_provider": "google",
                "max_articles": 8
            }
        }

class NewsResponse(BaseModel):
    job_id: str = Field(..., description="Unique job identifier")
    status: JobStatus = Field(..., description="Current job status")
    message: str = Field(..., description="Status message")
    created_at: datetime = Field(..., description="Job creation timestamp")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion time")
    
    class Config:
        # ✅ FIXED: Updated for Pydantic V2
        json_schema_extra = {
            "example": {
                "job_id": "news_20250928_210000_abc123",
                "status": "running",
                "message": "Research in progress...",
                "created_at": "2025-09-28T21:00:00Z",
                "estimated_completion": "2025-09-28T21:05:00Z"
            }
        }

class StatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    progress: Optional[float] = Field(None, description="Progress percentage (0-100)")
    current_step: Optional[str] = Field(None, description="Current processing step")
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
class ResultsResponse(BaseModel):
    job_id: str
    status: JobStatus
    topic: str
    research_summary: Optional[str] = None
    final_report: Optional[str] = None
    research_file: Optional[str] = Field(None, description="Path to research markdown file")
    report_file: Optional[str] = Field(None, description="Path to final report markdown file")
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

class ConfigResponse(BaseModel):
    current_llm: LLMProvider
    available_llms: List[LLMProvider]
    newsdata_configured: bool
    google_configured: bool
    ollama_available: bool
    
class LLMSwitchRequest(BaseModel):
    provider: LLMProvider = Field(..., description="LLM provider to switch to")
    
    class Config:
        # ✅ FIXED: Updated for Pydantic V2
        json_schema_extra = {
            "example": {
                "provider": "google"
            }
        }

class ErrorResponse(BaseModel):
    error: str
    message: str
    timestamp: datetime
    
    class Config:
        # ✅ FIXED: Updated for Pydantic V2
        json_schema_extra = {
            "example": {
                "error": "validation_error",
                "message": "Topic is required and cannot be empty",
                "timestamp": "2025-09-28T21:00:00Z"
            }
        }
