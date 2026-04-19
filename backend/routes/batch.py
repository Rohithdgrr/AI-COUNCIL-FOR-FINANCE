"""
Batch Operations API Routes

Endpoints for batch processing operations.
"""

from fastapi import APIRouter, HTTPException
import logging

from backend.api.batch import (
    batch_manager,
    BatchJobRequest,
    BatchJobResponse,
    BatchJobStatusResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/batch", tags=["Batch Operations"])


@router.post("/jobs", response_model=BatchJobResponse)
async def create_batch_job(request: BatchJobRequest):
    """
    Create a new batch job.
    
    Process multiple items in a single request.
    10x faster than sequential API calls.
    """
    try:
        if not request.items:
            raise HTTPException(status_code=400, detail="Items list cannot be empty")
        
        if len(request.items) > 1000:
            raise HTTPException(
                status_code=400,
                detail="Maximum 1000 items per batch job"
            )
        
        response = await batch_manager.create_job(request)
        
        return response
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Failed to create batch job: {e}")
        raise HTTPException(status_code=500, detail="Failed to create batch job")


@router.get("/jobs/{job_id}", response_model=BatchJobStatusResponse)
async def get_batch_job_status(job_id: str):
    """
    Get status of a batch job.
    
    Returns progress, results, and completion status.
    """
    try:
        status = await batch_manager.get_job_status(job_id)
        
        if not status:
            raise HTTPException(status_code=404, detail="Batch job not found")
        
        return status
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Failed to get batch job status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get job status")
