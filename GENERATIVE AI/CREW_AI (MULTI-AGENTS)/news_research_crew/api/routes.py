from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import FileResponse
import os
from datetime import datetime, timedelta  # ✅ Add timedelta import
from typing import List

from .models import (
    NewsRequest, NewsResponse, StatusResponse, ResultsResponse, 
    ConfigResponse, LLMSwitchRequest, ErrorResponse, JobStatus, LLMProvider
)
from .background_tasks import JobManager

router = APIRouter()

# Global job manager instance
job_manager = JobManager()

@router.post("/research", response_model=NewsResponse)
async def start_research(
    request: NewsRequest,
    background_tasks: BackgroundTasks
):
    """Start a new news research job"""
    
    # Check if we can start a new job
    if not job_manager.can_start_new_job():
        raise HTTPException(
            status_code=429,
            detail="Too many concurrent jobs. Please try again later."
        )
    
    # Validate configuration
    if not os.getenv('NEWSDATA_API_KEY'):
        raise HTTPException(
            status_code=500,
            detail="NewsData.io API key not configured"
        )
    
    if request.llm_provider == LLMProvider.google and not os.getenv('GOOGLE_API_KEY'):
        raise HTTPException(
            status_code=500,
            detail="Google API key not configured"
        )
    
    # Create job
    job_id = job_manager.create_job(
        topic=request.topic,
        llm_provider=request.llm_provider.value
    )
    
    # Start background task
    background_tasks.add_task(job_manager.execute_job, job_id)
    
    # ✅ FIXED: Use timedelta for proper datetime arithmetic
    return NewsResponse(
        job_id=job_id,
        status=JobStatus.pending,
        message="Research job created and queued for processing",
        created_at=datetime.now(),
        estimated_completion=datetime.now() + timedelta(minutes=5)  # ✅ Proper way
    )

@router.get("/status/{job_id}", response_model=StatusResponse)
async def get_job_status(job_id: str):
    """Get current status of a research job"""
    
    job = job_manager.get_job_status(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return StatusResponse(
        job_id=job["id"],
        status=job["status"],
        progress=job["progress"],
        current_step=job["current_step"],
        created_at=job["created_at"],
        started_at=job["started_at"],
        completed_at=job["completed_at"],
        error_message=job["error_message"]
    )

@router.get("/results/{job_id}", response_model=ResultsResponse)
async def get_job_results(job_id: str):
    """Get results of a completed research job"""
    
    job = job_manager.get_job_results(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return ResultsResponse(
        job_id=job["id"],
        status=job["status"],
        topic=job["topic"],
        research_summary=job.get("research_content"),
        final_report=job.get("report_content"),
        research_file=job["research_file"],
        report_file=job["report_file"],
        metadata={
            "llm_provider": job["llm_provider"],
            "progress": job["progress"],
            "current_step": job["current_step"]
        },
        created_at=job["created_at"],
        completed_at=job["completed_at"]
    )

@router.get("/download/{job_id}/{file_type}")
async def download_file(job_id: str, file_type: str):
    """Download generated files (research or report)"""
    
    job = job_manager.get_job_status(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job["status"] != JobStatus.completed:
        raise HTTPException(status_code=400, detail="Job not completed yet")
    
    if file_type == "research" and job["research_file"]:
        file_path = job["research_file"]
    elif file_type == "report" and job["report_file"]:
        file_path = job["report_file"]
    else:
        raise HTTPException(status_code=404, detail="File not found")
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    return FileResponse(
        path=file_path,
        filename=os.path.basename(file_path),
        media_type='text/markdown'
    )

@router.get("/config", response_model=ConfigResponse)
async def get_config():
    """Get current configuration"""
    
    current_llm = LLMProvider(os.getenv('LLM_PROVIDER', 'google'))
    
    return ConfigResponse(
        current_llm=current_llm,
        available_llms=[LLMProvider.google, LLMProvider.ollama],
        newsdata_configured=bool(os.getenv('NEWSDATA_API_KEY')),
        google_configured=bool(os.getenv('GOOGLE_API_KEY')),
        ollama_available=True  # Assume available for now
    )

@router.post("/config/llm")
async def switch_llm(request: LLMSwitchRequest):
    """Switch LLM provider"""
    
    if request.provider == LLMProvider.google and not os.getenv('GOOGLE_API_KEY'):
        raise HTTPException(
            status_code=400,
            detail="Google API key not configured"
        )
    
    os.environ['LLM_PROVIDER'] = request.provider.value
    
    return {
        "message": f"Switched to {request.provider.value}",
        "current_llm": request.provider.value,
        "timestamp": datetime.now()
    }

@router.get("/jobs")
async def list_jobs():
    """List all jobs (for admin/debugging)"""
    
    jobs = []
    for job_id, job in job_manager.jobs.items():
        jobs.append({
            "job_id": job_id,
            "topic": job["topic"],
            "status": job["status"],
            "created_at": job["created_at"],
            "llm_provider": job["llm_provider"]
        })
    
    return {
        "jobs": jobs,
        "running_count": job_manager.get_running_jobs_count(),
        "total_count": len(jobs)
    }

@router.delete("/jobs/{job_id}")
async def cancel_job(job_id: str):
    """Cancel a running job"""
    
    job = job_manager.get_job_status(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job["status"] == JobStatus.running:
        job["status"] = JobStatus.failed
        job["error_message"] = "Job cancelled by user"
        job["completed_at"] = datetime.now()
    
    return {"message": "Job cancelled", "job_id": job_id}

@router.post("/cleanup")
async def cleanup_old_jobs():
    """Clean up old completed jobs"""
    
    removed_count = job_manager.cleanup_old_jobs(max_age_hours=24)
    
    return {
        "message": f"Cleaned up {removed_count} old jobs",
        "removed_count": removed_count,
        "timestamp": datetime.now()
    }
