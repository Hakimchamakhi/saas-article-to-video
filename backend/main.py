"""
FastAPI Application for Blog-to-Video Converter
Handles API endpoints for video generation, status checking, and file serving.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, HttpUrl, Field
from typing import Literal
from celery.result import AsyncResult
import os
from pathlib import Path

from worker import celery_app, generate_video_task

app = FastAPI(title="Blog to Video Converter API")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure static directory exists
STATIC_DIR = Path(__file__).parent / "static"
STATIC_DIR.mkdir(exist_ok=True)

# Request/Response Models
class VideoGenerationRequest(BaseModel):
    url: HttpUrl
    video_format: Literal["landscape", "portrait"] = Field(
        default="landscape",
        description="Video format: 'landscape' for YouTube (16:9) or 'portrait' for TikTok/Shorts (9:16)"
    )


class VideoGenerationResponse(BaseModel):
    job_id: str


class StatusResponse(BaseModel):
    status: str
    error: str = None
    video_url: str = None
    progress: str = None
    percentage: int = 0
    current_step: str = None
    total_steps: int = 5


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Blog to Video Converter API", "status": "running"}


@app.post("/api/generate-video", response_model=VideoGenerationResponse)
async def generate_video(request: VideoGenerationRequest):
    """
    Initiates video generation from a blog article URL.
    Returns a job_id for tracking the task status.
    """
    try:
        # Convert HttpUrl to string
        url = str(request.url)
        video_format = request.video_format

        # Dispatch the Celery task with video format
        task = generate_video_task.delay(url, video_format)

        return VideoGenerationResponse(job_id=task.id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initiate video generation: {str(e)}")


@app.get("/api/status/{job_id}", response_model=StatusResponse)
async def get_status(job_id: str):
    """
    Check the status of a video generation task.
    Returns: pending, processing, failed, or complete with video_url.
    """
    try:
        # Get the task result from Celery
        task_result = AsyncResult(job_id, app=celery_app)

        if task_result.state == "PENDING":
            return StatusResponse(
                status="pending",
                progress="Task is queued...",
                percentage=0,
                current_step="Waiting in queue",
                total_steps=5
            )
        elif task_result.state == "PROGRESS":
            # Custom state we'll use to report progress
            task_info = task_result.info or {}
            progress_info = task_info.get("progress", "Processing...")
            percentage = task_info.get("percentage", 0)
            current_step = task_info.get("current_step", "Processing...")
            total_steps = task_info.get("total_steps", 5)

            return StatusResponse(
                status="processing",
                progress=progress_info,
                percentage=percentage,
                current_step=current_step,
                total_steps=total_steps
            )
        elif task_result.state == "FAILURE":
            error_message = str(task_result.info)
            return StatusResponse(status="failed", error=error_message)
        elif task_result.state == "SUCCESS":
            # Task completed successfully
            result = task_result.result
            video_filename = result.get("video_filename")
            video_url = f"/api/download/{video_filename}"
            return StatusResponse(status="complete", video_url=video_url)
        else:
            # Unknown state
            return StatusResponse(status="processing", progress=f"Task state: {task_result.state}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking task status: {str(e)}")


@app.get("/api/download/{filename}")
async def download_video(filename: str):
    """
    Serve the generated video file.
    """
    file_path = STATIC_DIR / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Video file not found")

    return FileResponse(
        path=file_path,
        media_type="video/mp4",
        filename=filename
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
