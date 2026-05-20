from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime


# User schemas
class UserBase(BaseModel):
    email: EmailStr
    username: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


class UserResponse(UserBase):
    id: int
    role: str
    is_active: bool
    is_verified: bool
    subscription_tier: str
    monthly_quota: int
    used_quota: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserProfileUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None


class UserProfileResponse(BaseModel):
    user: UserResponse
    subscription: Optional[Dict[str, Any]] = None


# Flight Log schemas
class FlightLogBase(BaseModel):
    filename: str
    file_type: str
    drone_model: Optional[str] = None


class FlightLogUpload(FlightLogBase):
    pass


class FlightLogResponse(FlightLogBase):
    id: int
    user_id: Optional[int]
    file_path: str
    file_size: int
    flight_duration: Optional[float]
    flight_date: Optional[datetime]
    is_processed: bool
    processing_status: str
    processing_error: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Flight Analysis schemas
class PidAnalysis(BaseModel):
    pitch: Optional[Dict[str, Any]] = None
    roll: Optional[Dict[str, Any]] = None
    yaw: Optional[Dict[str, Any]] = None


class GpsDrift(BaseModel):
    max_drift: float
    avg_drift: float
    problematic_areas: List[Dict[str, Any]]


class VibrationAnalysis(BaseModel):
    max_vibration: float
    avg_vibration: float
    peaks: List[Dict[str, Any]]


class MotorAnomalies(BaseModel):
    motor_1: Optional[Dict[str, Any]] = None
    motor_2: Optional[Dict[str, Any]] = None
    motor_3: Optional[Dict[str, Any]] = None
    motor_4: Optional[Dict[str, Any]] = None


class FlightAnalysisBase(BaseModel):
    flight_log_id: int
    overall_score: Optional[float] = None
    efficiency_score: Optional[float] = None
    stability_score: Optional[float] = None
    risk_level: str = "low"
    pid_analysis: Optional[PidAnalysis] = None
    gps_drift: Optional[GpsDrift] = None
    vibration_analysis: Optional[VibrationAnalysis] = None
    motor_anomalies: Optional[MotorAnomalies] = None
    ai_analysis: Optional[str] = None
    recommendations: Optional[List[str]] = None


class FlightAnalysisResponse(FlightAnalysisBase):
    id: int
    user_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AnalysisRequest(BaseModel):
    flight_log_id: int


# Subscription schemas
class SubscriptionPlanResponse(BaseModel):
    id: int
    name: str
    display_name: str
    description: Optional[str]
    price_monthly: float
    price_yearly: float
    monthly_quota: int
    max_file_size: int
    ai_analysis_enabled: bool
    priority_support: bool
    api_access: bool
    team_members: int
    
    class Config:
        from_attributes = True


class SubscriptionUpdate(BaseModel):
    plan_id: Optional[int] = None
    tier: Optional[str] = None


# API Response
class MessageResponse(BaseModel):
    message: str


class ErrorResponse(BaseModel):
    detail: str


# Drone Schemas
class DroneConnectRequest(BaseModel):
    drone_id: str
    connection_uri: Optional[str] = "udp://:14540"


class DroneResponse(BaseModel):
    drone_id: str
    status: str
    connection_uri: Optional[str] = None
    connected_at: Optional[str] = None


class DronePosition(BaseModel):
    latitude: float
    longitude: float
    absolute_altitude: float
    relative_altitude: float


class DroneVelocity(BaseModel):
    north: float
    east: float
    down: float


class DroneAttitude(BaseModel):
    roll: float
    pitch: float
    yaw: float


class DroneBattery(BaseModel):
    voltage: float
    remaining: float
    current: float


class DroneTelemetry(BaseModel):
    position: DronePosition
    velocity: DroneVelocity
    attitude: DroneAttitude
    battery: DroneBattery
    armed: bool
    in_air: bool
    flight_mode: str
    last_update: Optional[str] = None


class DroneStatusResponse(BaseModel):
    drone_id: str
    status: str
    connection_uri: str
    connected_at: Optional[str] = None
    telemetry: DroneTelemetry


class DroneActionRequest(BaseModel):
    drone_id: str


class DroneTakeoffRequest(BaseModel):
    drone_id: str
    altitude: Optional[float] = 2.0


class DronePositionRequest(BaseModel):
    drone_id: str
    latitude: float
    longitude: float
    altitude: float


class DroneActionResponse(BaseModel):
    success: bool
    message: str
    details: Optional[Dict[str, Any]] = None


class DroneListResponse(BaseModel):
    drones: List[DroneResponse]
