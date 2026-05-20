"""
HKAIC SaaS - Drone Control API
RESTful API endpoints for drone connection and control
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Dict, Any
import logging

from app.database import get_db
from app.schemas import (
    DroneConnectRequest,
    DroneResponse,
    DroneStatusResponse,
    DroneActionRequest,
    DroneTakeoffRequest,
    DronePositionRequest,
    DroneActionResponse,
    DroneListResponse,
    MessageResponse
)
from app.auth import get_current_user
from app.models import User
from app.drone_manager import drone_manager, DroneConnectionStatus
from app.audit_logger import log_drone_action
from app.main import limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/drone", tags=["Drone Control"])


def get_client_ip(request: Request) -> str:
    """获取客户端IP地址"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.post("/connect", response_model=DroneActionResponse, status_code=status.HTTP_200_OK)
async def connect_to_drone(
    request_body: DroneConnectRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    request: Request = None
):
    """
    Connect to a drone
    
    ⚠️ SECURITY NOTE: Only connect to trusted drone systems.
    Connection to arbitrary network addresses is not allowed.
    
    Requires authentication
    """
    ip_address = get_client_ip(request) if request else "unknown"
    logger.info(f"User {current_user.id} connecting to drone {request_body.drone_id}")
    
    try:
        result = await drone_manager.connect_drone(
            drone_id=request_body.drone_id,
            connection_uri=request_body.connection_uri,
            user_id=current_user.id
        )
        
        # 记录审计日志
        log_result = "success" if result.get("success", False) else "failure"
        log_drone_action(
            action="connect",
            user_id=current_user.id,
            drone_id=request_body.drone_id,
            result=log_result,
            details=result,
            ip_address=ip_address
        )
        
        if not result.get("success", False):
            status_code = status.HTTP_400_BAD_REQUEST
            if result.get("status") == "validation_failed":
                status_code = status.HTTP_400_BAD_REQUEST
            elif result.get("status") == "error":
                status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            elif result.get("status") == "limit_reached":
                status_code = status.HTTP_429_TOO_MANY_REQUESTS
            
            raise HTTPException(
                status_code=status_code,
                detail=result.get("message", "Connection failed")
            )
        
        return DroneActionResponse(
            success=result.get("success", False),
            message=result.get("message", ""),
            details=result
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to connect to drone: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Connection failed. Please try again."
        )


@router.post("/disconnect", response_model=DroneActionResponse, status_code=status.HTTP_200_OK)
async def disconnect_from_drone(
    request: DroneActionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Disconnect from a drone
    
    Requires authentication
    """
    logger.info(f"User {current_user.id} disconnecting from drone {request.drone_id}")
    
    try:
        result = await drone_manager.disconnect_drone(request.drone_id)
        
        return DroneActionResponse(
            success=result.get("success", False),
            message=result.get("message", "")
        )
    except Exception as e:
        logger.error(f"Failed to disconnect: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Disconnection failed: {str(e)}"
        )


@router.get("/list", response_model=DroneListResponse, status_code=status.HTTP_200_OK)
async def list_drones(
    current_user: User = Depends(get_current_user)
):
    """
    List all registered drones
    
    Requires authentication
    """
    try:
        drones = drone_manager.list_drones()
        
        drone_responses = [
            DroneResponse(
                drone_id=d["drone_id"],
                status=d["status"],
                connection_uri=d.get("connection_uri"),
                connected_at=d.get("connected_at")
            )
            for d in drones
        ]
        
        return DroneListResponse(drones=drone_responses)
    except Exception as e:
        logger.error(f"Failed to list drones: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list drones: {str(e)}"
        )


@router.get("/status/{drone_id}", response_model=DroneStatusResponse, status_code=status.HTTP_200_OK)
async def get_drone_status(
    drone_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed status of a specific drone
    
    Requires authentication
    """
    try:
        status_data = await drone_manager.get_drone_status(drone_id)
        
        if not status_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Drone {drone_id} not found"
            )
        
        # Map to our response model
        telemetry_data = status_data["telemetry"]
        
        return DroneStatusResponse(
            drone_id=status_data["drone_id"],
            status=status_data["status"],
            connection_uri=status_data["connection_uri"],
            connected_at=status_data.get("connected_at"),
            telemetry={
                "position": telemetry_data["position"],
                "velocity": telemetry_data["velocity"],
                "attitude": telemetry_data["attitude"],
                "battery": telemetry_data["battery"],
                "armed": telemetry_data["armed"],
                "in_air": telemetry_data["in_air"],
                "flight_mode": telemetry_data["flight_mode"],
                "last_update": telemetry_data.get("last_update")
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get drone status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get status: {str(e)}"
        )


@router.post("/arm", response_model=DroneActionResponse, status_code=status.HTTP_200_OK)
@limiter.limit("10/minute")  # 每分钟最多10次
async def arm_drone(
    request_body: DroneActionRequest,
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    """
    Arm the drone
    
    ⚠️ SAFETY WARNING: This sends actual flight commands to a real drone.
    Ensure proper safety measures are in place before use.
    
    Requires authentication
    """
    ip_address = get_client_ip(request) if request else "unknown"
    logger.info(f"User {current_user.id} arming drone {request_body.drone_id}")
    
    try:
        result = await drone_manager.arm_drone(request_body.drone_id)
        
        # 记录审计日志
        log_result = "success" if result.get("success", False) else "failure"
        log_drone_action(
            action="arm",
            user_id=current_user.id,
            drone_id=request_body.drone_id,
            result=log_result,
            details=result,
            ip_address=ip_address
        )
        
        return DroneActionResponse(
            success=result.get("success", False),
            message=result.get("message", ""),
            details=result
        )
    except Exception as e:
        logger.error(f"Failed to arm drone: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Arming failed: {str(e)}"
        )


@router.post("/disarm", response_model=DroneActionResponse, status_code=status.HTTP_200_OK)
async def disarm_drone(
    request: DroneActionRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Disarm the drone
    
    Requires authentication
    """
    logger.info(f"User {current_user.id} disarming drone {request.drone_id}")
    
    try:
        result = await drone_manager.disarm_drone(request.drone_id)
        
        return DroneActionResponse(
            success=result.get("success", False),
            message=result.get("message", ""),
            details=result
        )
    except Exception as e:
        logger.error(f"Failed to disarm drone: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Disarming failed: {str(e)}"
        )


@router.post("/takeoff", response_model=DroneActionResponse, status_code=status.HTTP_200_OK)
@limiter.limit("10/minute")  # 每分钟最多10次
async def takeoff_drone(
    request: DroneTakeoffRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Command drone to takeoff
    
    ⚠️ SAFETY WARNING: This sends actual flight commands to a real drone.
    Ensure proper safety measures are in place before use.
    
    Requires authentication
    """
    logger.info(f"User {current_user.id} commanding takeoff for drone {request.drone_id}")
    
    try:
        result = await drone_manager.takeoff_drone(
            request.drone_id,
            request.altitude
        )
        
        if not result.get("success", False):
            status_code = status.HTTP_400_BAD_REQUEST
            if result.get("status") == "validation_failed":
                status_code = status.HTTP_400_BAD_REQUEST
            elif "not connected" in result.get("message", "").lower():
                status_code = status.HTTP_400_BAD_REQUEST
            elif "not found" in result.get("message", "").lower():
                status_code = status.HTTP_404_NOT_FOUND
            else:
                status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            
            raise HTTPException(
                status_code=status_code,
                detail=result.get("message", "Takeoff failed")
            )
        
        return DroneActionResponse(
            success=result.get("success", False),
            message=result.get("message", ""),
            details=result
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to takeoff: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Takeoff command failed. Please try again."
        )


@router.post("/land", response_model=DroneActionResponse, status_code=status.HTTP_200_OK)
async def land_drone(
    request: DroneActionRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Command drone to land
    
    Requires authentication
    """
    logger.info(f"User {current_user.id} commanding landing for drone {request.drone_id}")
    
    try:
        result = await drone_manager.land_drone(request.drone_id)
        
        return DroneActionResponse(
            success=result.get("success", False),
            message=result.get("message", ""),
            details=result
        )
    except Exception as e:
        logger.error(f"Failed to land: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Landing failed: {str(e)}"
        )


@router.post("/return-home", response_model=DroneActionResponse, status_code=status.HTTP_200_OK)
async def return_to_home(
    request: DroneActionRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Command drone to return to home
    
    Requires authentication
    """
    logger.info(f"User {current_user.id} commanding return to home for drone {request.drone_id}")
    
    try:
        result = await drone_manager.return_to_home(request.drone_id)
        
        return DroneActionResponse(
            success=result.get("success", False),
            message=result.get("message", ""),
            details=result
        )
    except Exception as e:
        logger.error(f"Failed to return home: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Return to home failed: {str(e)}"
        )


@router.post("/goto", response_model=DroneActionResponse, status_code=status.HTTP_200_OK)
@limiter.limit("20/minute")  # 每分钟最多20次
async def goto_position(
    request_body: DronePositionRequest,
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    """
    Send position control command to drone
    
    ⚠️ SAFETY WARNING: This sends actual flight commands to a real drone.
    Ensure coordinates are within safe and legal flying areas.
    
    Requires authentication
    """
    ip_address = get_client_ip(request) if request else "unknown"
    logger.info(f"User {current_user.id} sending position command to drone {request_body.drone_id}")
    
    try:
        result = await drone_manager.set_position(
            request_body.drone_id,
            request_body.latitude,
            request_body.longitude,
            request_body.altitude
        )
        
        # 记录审计日志
        log_result = "success" if result.get("success", False) else "failure"
        log_drone_action(
            action="goto",
            user_id=current_user.id,
            drone_id=request_body.drone_id,
            result=log_result,
            details={
                "latitude": request_body.latitude,
                "longitude": request_body.longitude,
                "altitude": request_body.altitude,
                **result
            },
            ip_address=ip_address
        )
        
        if not result.get("success", False):
            status_code = status.HTTP_400_BAD_REQUEST
            if result.get("status") == "validation_failed":
                status_code = status.HTTP_400_BAD_REQUEST
            elif "not found" in result.get("message", "").lower():
                status_code = status.HTTP_404_NOT_FOUND
            else:
                status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            
            raise HTTPException(
                status_code=status_code,
                detail=result.get("message", "Position command failed")
            )
        
        return DroneActionResponse(
            success=result.get("success", False),
            message=result.get("message", ""),
            details=result
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send position command: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Position command failed. Please try again."
        )


@router.post("/emergency-stop", response_model=DroneActionResponse, status_code=status.HTTP_200_OK)
async def emergency_stop_all(
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    """
    🚨 EMERGENCY STOP - Land all drones immediately
    
    ⚠️ CRITICAL SAFETY COMMAND: This will immediately land ALL connected drones.
    Use only in emergency situations!
    
    Requires authentication
    """
    ip_address = get_client_ip(request) if request else "unknown"
    logger.critical(f"EMERGENCY STOP triggered by user {current_user.id} from {ip_address}")
    
    try:
        result = await drone_manager.emergency_stop_all()
        
        # 记录紧急操作的审计日志
        for drone_result in result.get("results", []):
            log_drone_action(
                action="emergency_stop",
                user_id=current_user.id,
                drone_id=drone_result["drone_id"],
                result="success" if drone_result["result"].get("success") else "failure",
                details=drone_result["result"],
                ip_address=ip_address
            )
        
        return DroneActionResponse(
            success=result.get("success", False),
            message=result.get("message", ""),
            details=result
        )
    except Exception as e:
        logger.error(f"Emergency stop failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Emergency stop failed. Please try again."
        )


@router.get("/statistics", status_code=status.HTTP_200_OK)
async def get_drone_statistics(
    current_user: User = Depends(get_current_user)
):
    """
    Get drone connection statistics
    
    Requires authentication
    """
    try:
        stats = drone_manager.get_statistics()
        return stats
    except Exception as e:
        logger.error(f"Failed to get statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve statistics"
        )
