import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional
import os
import sys
import traceback
from enum import Enum

# Add src to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.crew import NewsResearchCrew
from api.models import JobStatus

class JobManager:
    def __init__(self):
        self.jobs: Dict[str, Dict] = {}
        self.max_concurrent_jobs = 3
        self.job_timeout_minutes = 15
    
    def create_job(self, topic: str, llm_provider: str = "google") -> str:
        """Create a new research job"""
        job_id = f"news_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        self.jobs[job_id] = {
            "id": job_id,
            "topic": topic,
            "llm_provider": llm_provider,
            "status": JobStatus.pending,
            "progress": 0.0,
            "current_step": "Initializing...",
            "created_at": datetime.now(),
            "started_at": None,
            "completed_at": None,
            "error_message": None,
            "result": None,
            "research_file": None,
            "report_file": None,
        }
        
        return job_id
    
    async def execute_job(self, job_id: str):
        """Execute a research job in the background"""
        if job_id not in self.jobs:
            return
        
        job = self.jobs[job_id]
        
        try:
            # Update job status
            job["status"] = JobStatus.running
            job["started_at"] = datetime.now()
            job["current_step"] = "Setting up research crew..."
            job["progress"] = 10.0
            
            # Set LLM provider
            os.environ['LLM_PROVIDER'] = job["llm_provider"]
            
            # Update progress
            job["current_step"] = "Initializing agents and tools..."
            job["progress"] = 20.0
            
            # Create and run crew
            crew = NewsResearchCrew(job["topic"])
            
            job["current_step"] = "Researching news articles..."
            job["progress"] = 40.0
            
            # Execute research (this might take a few minutes)
            result = crew.run()
            
            job["current_step"] = "Generating final report..."
            job["progress"] = 80.0
            
            # Find generated files
            topic_clean = job["topic"].replace(' ', '_').lower()
            output_files = [f for f in os.listdir("outputs") if topic_clean in f.lower()]
            
            research_files = [f for f in output_files if "research" in f]
            report_files = [f for f in output_files if "final_report" in f or "report" in f]
            
            job["research_file"] = f"outputs/{research_files[0]}" if research_files else None
            job["report_file"] = f"outputs/{report_files[0]}" if report_files else None
            
            # Complete job
            job["status"] = JobStatus.completed
            job["completed_at"] = datetime.now()
            job["current_step"] = "Research completed successfully!"
            job["progress"] = 100.0
            job["result"] = str(result) if result else "Research completed"
            
        except Exception as e:
            # Handle errors
            job["status"] = JobStatus.failed
            job["completed_at"] = datetime.now()
            job["error_message"] = str(e)
            job["current_step"] = f"Error: {str(e)}"
            job["progress"] = 0.0
            
            # Log error for debugging
            print(f"Job {job_id} failed: {str(e)}")
            traceback.print_exc()
    
    def get_job_status(self, job_id: str) -> Optional[Dict]:
        """Get current job status"""
        return self.jobs.get(job_id)
    
    def get_job_results(self, job_id: str) -> Optional[Dict]:
        """Get job results with file content"""
        job = self.jobs.get(job_id)
        if not job or job["status"] != JobStatus.completed:
            return job
        
        # Read file contents
        try:
            if job["research_file"] and os.path.exists(job["research_file"]):
                with open(job["research_file"], 'r', encoding='utf-8') as f:
                    job["research_content"] = f.read()
            
            if job["report_file"] and os.path.exists(job["report_file"]):
                with open(job["report_file"], 'r', encoding='utf-8') as f:
                    job["report_content"] = f.read()
                    
        except Exception as e:
            print(f"Error reading files for job {job_id}: {str(e)}")
        
        return job
    
    def cleanup_old_jobs(self, max_age_hours: int = 24):
        """Clean up old completed jobs"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        jobs_to_remove = []
        for job_id, job in self.jobs.items():
            if job["completed_at"] and job["completed_at"] < cutoff_time:
                jobs_to_remove.append(job_id)
        
        for job_id in jobs_to_remove:
            del self.jobs[job_id]
        
        return len(jobs_to_remove)
    
    def get_running_jobs_count(self) -> int:
        """Get count of currently running jobs"""
        return sum(1 for job in self.jobs.values() if job["status"] == JobStatus.running)
    
    def can_start_new_job(self) -> bool:
        """Check if we can start a new job"""
        return self.get_running_jobs_count() < self.max_concurrent_jobs
