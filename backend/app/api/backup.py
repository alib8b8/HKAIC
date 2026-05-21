"""
User Tuning Backup API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
from app.database import get_db
from app.models import User, TuningBackup, TuningSession
from app.auth import get_current_user

router = APIRouter(prefix="/api/backup", tags=["Backup"])


class TuningBackupCreate(BaseModel):
    name: str
    description: Optional[str] = None
    params: Dict[str, float]
    presets: Optional[Dict[str, Dict[str, float]]] = None
    drone_model: Optional[str] = None
    firmware_version: Optional[str] = None


class TuningBackupResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    params: Dict[str, float]
    presets: Optional[Dict[str, Dict[str, float]]]
    drone_model: Optional[str]
    firmware_version: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TuningSessionCreate(BaseModel):
    session_type: str = "adjustment"
    snapshots: Optional[List[Dict[str, Any]]] = None
    conversations: Optional[List[Dict[str, str]]] = None
    backup_id: Optional[int] = None


class TuningSessionResponse(BaseModel):
    id: int
    session_type: str
    snapshots: Optional[List[Dict[str, Any]]]
    conversations: Optional[List[Dict[str, str]]]
    backup_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


@router.post("/save", response_model=TuningBackupResponse, status_code=status.HTTP_201_CREATED)
async def save_tuning_backup(
    backup_data: TuningBackupCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Save a new tuning parameter backup"""
    db_backup = TuningBackup(
        user_id=current_user.id,
        name=backup_data.name,
        description=backup_data.description,
        params=backup_data.params,
        presets=backup_data.presets,
        drone_model=backup_data.drone_model,
        firmware_version=backup_data.firmware_version
    )
    
    db.add(db_backup)
    db.commit()
    db.refresh(db_backup)
    
    return db_backup


@router.get("/list", response_model=List[TuningBackupResponse])
async def list_tuning_backups(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all tuning backups for current user"""
    backups = db.query(TuningBackup).filter(
        TuningBackup.user_id == current_user.id
    ).order_by(TuningBackup.created_at.desc()).all()
    
    return backups


@router.get("/{backup_id}", response_model=TuningBackupResponse)
async def get_tuning_backup(
    backup_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific tuning backup"""
    backup = db.query(TuningBackup).filter(
        TuningBackup.id == backup_id,
        TuningBackup.user_id == current_user.id
    ).first()
    
    if not backup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Backup not found"
        )
    
    return backup


@router.delete("/{backup_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tuning_backup(
    backup_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a tuning backup"""
    backup = db.query(TuningBackup).filter(
        TuningBackup.id == backup_id,
        TuningBackup.user_id == current_user.id
    ).first()
    
    if not backup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Backup not found"
        )
    
    db.delete(backup)
    db.commit()


@router.post("/session", response_model=TuningSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_tuning_session(
    session_data: TuningSessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new tuning session"""
    db_session = TuningSession(
        user_id=current_user.id,
        session_type=session_data.session_type,
        snapshots=session_data.snapshots,
        conversations=session_data.conversations,
        backup_id=session_data.backup_id
    )
    
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    
    return db_session


@router.get("/sessions/list", response_model=List[TuningSessionResponse])
async def list_tuning_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all tuning sessions for current user"""
    sessions = db.query(TuningSession).filter(
        TuningSession.user_id == current_user.id
    ).order_by(TuningSession.created_at.desc()).all()
    
    return sessions


@router.get("/stats/summary")
async def get_backup_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get backup statistics for current user"""
    total_backups = db.query(TuningBackup).filter(
        TuningBackup.user_id == current_user.id
    ).count()
    
    total_sessions = db.query(TuningSession).filter(
        TuningSession.user_id == current_user.id
    ).count()
    
    latest_backup = db.query(TuningBackup).filter(
        TuningBackup.user_id == current_user.id
    ).order_by(TuningBackup.created_at.desc()).first()
    
    return {
        "total_backups": total_backups,
        "total_sessions": total_sessions,
        "latest_backup": latest_backup.created_at if latest_backup else None,
        "storage_used_mb": total_backups * 0.01
    }
