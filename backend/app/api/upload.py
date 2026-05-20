from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from sqlalchemy.orm import Session
import os
import uuid
import re
import logging
from datetime import datetime
from app.database import get_db
from app.config import settings
from app.schemas import FlightLogResponse, MessageResponse
from app.models import FlightLog, User
from app.auth import get_current_user
import shutil

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/upload", tags=["Upload"])


@router.post("/", response_model=FlightLogResponse, status_code=status.HTTP_201_CREATED)
async def upload_flight_log(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload a flight log file for analysis.
    Supported formats: .csv, .ulg, .bbl
    Requires authentication.
    """
    # Validate file extension
    filename = file.filename
    if not filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided"
        )
    
    ext = os.path.splitext(filename)[1].lower().lstrip('.')
    valid_extensions = ['csv', 'ulg', 'bbl']
    if ext not in valid_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file format. Supported formats: {', '.join(valid_extensions)}"
        )
    
    # Check file size
    file_content = await file.read()
    file_size = len(file_content)
    
    # Get user's plan limits
    from app.database import SubscriptionPlan
    plan = db.query(SubscriptionPlan).filter(
        SubscriptionPlan.name == current_user.subscription_tier).first()
    max_size = plan.max_file_size if plan else settings.max_upload_size
    
    if file_size > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {max_size} bytes"
        )
    
    # Clean filename to prevent security issues
    safe_filename = re.sub(r'[^\w\-_.]', '_', filename)
    
    # Create user-specific upload directory
    user_upload_dir = os.path.join(settings.upload_dir, str(current_user.id))
    os.makedirs(user_upload_dir, exist_ok=True)
    
    # Save file with unique name
    unique_filename = f"{uuid.uuid4()}_{safe_filename}"
    file_path = os.path.join(user_upload_dir, unique_filename)
    
    with open(file_path, "wb") as f:
        f.write(file_content)
    
    # Create database record with user association
    flight_log = FlightLog(
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        filename=safe_filename,  # Save the safe filename
        file_type=ext,
        file_path=file_path,
        file_size=file_size,
        processing_status="pending",
        is_processed=False
    )
    
    db.add(flight_log)
    db.commit()
    db.refresh(flight_log)
    
    logger.info(f"User {current_user.id} uploaded file: {safe_filename}")
    
    return flight_log


@router.get("/logs", response_model=list[FlightLogResponse])
async def list_uploaded_logs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List current user's uploaded flight logs"""
    logs = db.query(FlightLog).filter(
        FlightLog.user_id == current_user.id
    ).order_by(FlightLog.created_at.desc()).all()
    return logs


@router.get("/logs/{log_id}", response_model=FlightLogResponse)
async def get_flight_log(
    log_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific flight log by ID (only own logs)"""
    log = db.query(FlightLog).filter(
        FlightLog.id == log_id,
        FlightLog.user_id == current_user.id
    ).first()
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Flight log not found"
        )
    return log


@router.delete("/logs/{log_id}", response_model=MessageResponse)
async def delete_flight_log(
    log_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a flight log (only own logs)"""
    log = db.query(FlightLog).filter(
        FlightLog.id == log_id,
        FlightLog.user_id == current_user.id
    ).first()
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Flight log not found"
        )
    
    # Delete file if exists
    file_deleted = False
    if os.path.exists(log.file_path):
        try:
            os.remove(log.file_path)
            file_deleted = True
            logger.info(f"Deleted file: {log.file_path}")
        except Exception as e:
            logger.error(f"Failed to delete file {log.file_path}: {e}")
            # Continue with db deletion even if file deletion fails
    
    db.delete(log)
    db.commit()
    
    logger.info(f"User {current_user.id} deleted flight log {log_id}")
    
    return {"message": "Flight log deleted successfully"}
