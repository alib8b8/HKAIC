from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any
import logging

from app.database import get_db, SubscriptionPlan
from app.schemas import FlightAnalysisResponse, AnalysisRequest, MessageResponse
from app.models import FlightLog, FlightAnalysis, User
from app.parsers import LogParserFactory, analyze_flight_data
from app.ai_service import OpenAIAnalysisService
from app.supabase_service import SupabaseService
from app.auth import get_current_user

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analysis", tags=["Analysis"])


@router.post("/", response_model=FlightAnalysisResponse, status_code=status.HTTP_201_CREATED)
async def analyze_flight_log(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Analyze a flight log. This will parse the log and generate comprehensive analysis.
    If OpenAI is configured, it will also generate AI-powered insights.
    Requires authentication and checks subscription quota.
    """
    # Get flight log (verify ownership)
    flight_log = db.query(FlightLog).filter(
        FlightLog.id == request.flight_log_id,
        FlightLog.user_id == current_user.id
    ).first()
    
    if not flight_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Flight log not found"
        )
    
    # Check if already processed
    existing_analysis = db.query(FlightAnalysis).filter(
        FlightAnalysis.flight_log_id == request.flight_log_id
    ).first()
    
    if existing_analysis:
        return existing_analysis
    
    # Check subscription quota
    if current_user.used_quota >= current_user.monthly_quota:
        logger.warning(f"User {current_user.id} exceeded monthly quota")
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Monthly quota exceeded. Please upgrade your subscription."
        )
    
    # Check if AI analysis is available
    plan = db.query(SubscriptionPlan).filter(
        SubscriptionPlan.name == current_user.subscription_tier).first()
    ai_enabled = plan.ai_analysis_enabled if plan else False
    
    # Update log status
    flight_log.processing_status = "processing"
    db.commit()
    
    logger.info(f"Starting analysis for user {current_user.id}, log {flight_log.id}")
    
    try:
        # Parse the log
        parser = LogParserFactory.get_parser(flight_log.file_type)
        parsed_data = parser.parse(flight_log.file_path)
        
        # Perform analysis
        analysis_data = analyze_flight_data(parsed_data)
        
        # Get AI analysis if enabled
        ai_service = OpenAIAnalysisService()
        ai_result = {"ai_analysis": None, "recommendations": None}
        
        if ai_enabled and ai_service.is_available():
            ai_result = await ai_service.analyze_flight(analysis_data)
        elif ai_enabled:
            # Fallback analysis even if OpenAI not available
            ai_result = ai_service._get_fallback_analysis(analysis_data)
        
        # Create analysis record
        analysis = FlightAnalysis(
            flight_log_id=request.flight_log_id,
            user_id=current_user.id,
            tenant_id=current_user.tenant_id,
            overall_score=analysis_data.get('overall_score'),
            efficiency_score=analysis_data.get('efficiency_score'),
            stability_score=analysis_data.get('stability_score'),
            risk_level=analysis_data.get('risk_level', 'low'),
            pid_analysis=analysis_data.get('pid_analysis'),
            gps_drift=analysis_data.get('gps_drift'),
            vibration_analysis=analysis_data.get('vibration_analysis'),
            motor_anomalies=analysis_data.get('motor_anomalies'),
            ai_analysis=ai_result.get('ai_analysis'),
            recommendations=ai_result.get('recommendations')
        )
        
        db.add(analysis)
        
        # Update log status and user quota
        flight_log.is_processed = True
        flight_log.processing_status = "completed"
        flight_log.flight_duration = analysis_data.get('flight_duration')
        current_user.used_quota += 1
        
        db.commit()
        db.refresh(analysis)
        
        logger.info(f"Analysis completed for user {current_user.id}, log {flight_log.id}, score: {analysis.overall_score}")
        
        # Save to Supabase in background if available
        supabase = SupabaseService()
        if supabase.is_available():
            background_tasks.add_task(
                supabase.save_analysis,
                analysis_data,
                request.flight_log_id
            )
        
        return analysis
        
    except Exception as e:
        flight_log.processing_status = "failed"
        flight_log.processing_error = str(e)
        db.commit()
        logger.error(f"Analysis failed for user {current_user.id}, log {flight_log.id}: {str(e)}")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )


@router.get("/{log_id}", response_model=FlightAnalysisResponse)
async def get_analysis(
    log_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get analysis results for a specific flight log (only own logs)"""
    analysis = db.query(FlightAnalysis).filter(
        FlightAnalysis.flight_log_id == log_id,
        FlightAnalysis.user_id == current_user.id
    ).first()
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found. Please request an analysis first."
        )
    
    return analysis


@router.get("/score/{log_id}", response_model=Dict[str, Any])
async def get_flight_score(
    log_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get just the flight scores and risk level (only own logs)"""
    analysis = db.query(FlightAnalysis).filter(
        FlightAnalysis.flight_log_id == log_id,
        FlightAnalysis.user_id == current_user.id
    ).first()
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found"
        )
    
    return {
        "overall_score": analysis.overall_score,
        "efficiency_score": analysis.efficiency_score,
        "stability_score": analysis.stability_score,
        "risk_level": analysis.risk_level
    }


@router.get("/recommendations/{log_id}", response_model=Dict[str, Any])
async def get_recommendations(
    log_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get AI recommendations for improving flight (only own logs)"""
    analysis = db.query(FlightAnalysis).filter(
        FlightAnalysis.flight_log_id == log_id,
        FlightAnalysis.user_id == current_user.id
    ).first()
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found"
        )
    
    return {
        "recommendations": analysis.recommendations,
        "ai_analysis": analysis.ai_analysis
    }


@router.get("/pid/{log_id}", response_model=Dict[str, Any])
async def get_pid_analysis(
    log_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get PID tuning analysis (only own logs)"""
    analysis = db.query(FlightAnalysis).filter(
        FlightAnalysis.flight_log_id == log_id,
        FlightAnalysis.user_id == current_user.id
    ).first()
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found"
        )
    
    return analysis.pid_analysis or {}


@router.get("/vibration/{log_id}", response_model=Dict[str, Any])
async def get_vibration_analysis(
    log_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get vibration analysis results (only own logs)"""
    analysis = db.query(FlightAnalysis).filter(
        FlightAnalysis.flight_log_id == log_id,
        FlightAnalysis.user_id == current_user.id
    ).first()
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found"
        )
    
    return analysis.vibration_analysis or {}


@router.get("/gps/{log_id}", response_model=Dict[str, Any])
async def get_gps_drift(
    log_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get GPS drift analysis (only own logs)"""
    analysis = db.query(FlightAnalysis).filter(
        FlightAnalysis.flight_log_id == log_id,
        FlightAnalysis.user_id == current_user.id
    ).first()
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found"
        )
    
    return analysis.gps_drift or {}


@router.get("/motors/{log_id}", response_model=Dict[str, Any])
async def get_motor_anomalies(
    log_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get motor anomaly detection results (only own logs)"""
    analysis = db.query(FlightAnalysis).filter(
        FlightAnalysis.flight_log_id == log_id,
        FlightAnalysis.user_id == current_user.id
    ).first()
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found"
        )
    
    return analysis.motor_anomalies or {}


@router.post("/re-analyze/{log_id}", response_model=FlightAnalysisResponse)
async def reanalyze_flight(
    log_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Re-run analysis on an existing flight log (only own logs)"""
    flight_log = db.query(FlightLog).filter(
        FlightLog.id == log_id,
        FlightLog.user_id == current_user.id
    ).first()
    if not flight_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Flight log not found"
        )
    
    # Delete existing analysis
    db.query(FlightAnalysis).filter(
        FlightAnalysis.flight_log_id == log_id
    ).delete()
    db.commit()
    
    # Decrement quota (we'll re-increment)
    if current_user.used_quota > 0:
        current_user.used_quota -= 1
        db.commit()
    
    # Use the existing analysis endpoint
    return await analyze_flight_log(
        AnalysisRequest(flight_log_id=log_id),
        background_tasks,
        current_user,
        db
    )
