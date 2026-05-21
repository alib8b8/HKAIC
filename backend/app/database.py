from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os
from app.config import settings

# Create engine
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String, nullable=True)
    
    # SaaS fields
    role = Column(String, default="user")  # user, admin, superadmin
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Tenant info (for multi-tenant)
    tenant_id = Column(String, nullable=True, index=True)
    
    # Subscription
    subscription_tier = Column(String, default="free")  # free, basic, pro, enterprise
    subscription_expires_at = Column(DateTime, nullable=True)
    monthly_quota = Column(Integer, default=5)  # Monthly analysis quota
    used_quota = Column(Integer, default=0)
    
    # Stripe integration (optional)
    stripe_customer_id = Column(String, nullable=True)
    stripe_subscription_id = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    flight_logs = relationship("FlightLog", back_populates="user", cascade="all, delete-orphan")
    analyses = relationship("FlightAnalysis", back_populates="user", cascade="all, delete-orphan")
    tuning_backups = relationship("TuningBackup", back_populates="user", cascade="all, delete-orphan")
    tuning_sessions = relationship("TuningSession", back_populates="user", cascade="all, delete-orphan")


class FlightLog(Base):
    __tablename__ = "flight_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    filename = Column(String, nullable=False)
    file_type = Column(String(20), nullable=False)  # bbl, ulg, csv
    file_path = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    
    # Tenant for multi-tenant isolation
    tenant_id = Column(String, nullable=True, index=True)
    
    # Flight metadata
    drone_model = Column(String, nullable=True)
    flight_duration = Column(Float, nullable=True)  # in seconds
    flight_date = Column(DateTime, nullable=True)
    
    # Analysis status
    is_processed = Column(Boolean, default=False)
    processing_status = Column(String, default="pending")  # pending, processing, completed, failed
    processing_error = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="flight_logs")
    analysis = relationship("FlightAnalysis", back_populates="flight_log", uselist=False, cascade="all, delete-orphan")


class FlightAnalysis(Base):
    __tablename__ = "flight_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    flight_log_id = Column(Integer, ForeignKey("flight_logs.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Tenant for multi-tenant isolation
    tenant_id = Column(String, nullable=True, index=True)
    
    # Overall score
    overall_score = Column(Float, nullable=True)
    efficiency_score = Column(Float, nullable=True)
    stability_score = Column(Float, nullable=True)
    risk_level = Column(String(20), default="low")  # low, medium, high, critical
    
    # PID Analysis
    pid_analysis = Column(JSON, nullable=True)
    
    # GPS Drift
    gps_drift = Column(JSON, nullable=True)
    
    # Vibration Analysis
    vibration_analysis = Column(JSON, nullable=True)
    
    # Motor Anomalies
    motor_anomalies = Column(JSON, nullable=True)
    
    # AI Analysis
    ai_analysis = Column(Text, nullable=True)
    recommendations = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="analyses")
    flight_log = relationship("FlightLog", back_populates="analysis")


class SubscriptionPlan(Base):
    """Subscription plan definitions"""
    __tablename__ = "subscription_plans"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)  # free, basic, pro, enterprise
    display_name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    
    # Pricing
    price_monthly = Column(Float, default=0.0)
    price_yearly = Column(Float, default=0.0)
    
    # Features
    monthly_quota = Column(Integer, default=5)
    max_file_size = Column(Integer, default=10 * 1024 * 1024)  # 10MB
    ai_analysis_enabled = Column(Boolean, default=False)
    priority_support = Column(Boolean, default=False)
    api_access = Column(Boolean, default=False)
    team_members = Column(Integer, default=1)
    
    # Stripe
    stripe_price_id_monthly = Column(String, nullable=True)
    stripe_price_id_yearly = Column(String, nullable=True)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class TuningBackup(Base):
    """User tuning parameter backups"""
    __tablename__ = "tuning_backups"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Backup metadata
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    
    # Tuning data (JSON format)
    params = Column(JSON, nullable=False)
    presets = Column(JSON, nullable=True)
    
    # Metadata
    drone_model = Column(String, nullable=True)
    firmware_version = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="tuning_backups")
    sessions = relationship("TuningSession", back_populates="backup")


class TuningSession(Base):
    """Individual tuning sessions"""
    __tablename__ = "tuning_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    backup_id = Column(Integer, ForeignKey("tuning_backups.id"), nullable=True)
    
    # Session data
    session_type = Column(String, default="adjustment")  # adjustment, preset, analysis
    
    # Snapshots
    snapshots = Column(JSON, nullable=True)
    
    # Conversations
    conversations = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="tuning_sessions")
    backup = relationship("TuningBackup", back_populates="sessions")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
    
    # Initialize default subscription plans
    db = SessionLocal()
    try:
        # Check if plans exist
        if db.query(SubscriptionPlan).count() == 0:
            default_plans = [
                SubscriptionPlan(
                    name="free",
                    display_name="Free",
                    description="Perfect for hobbyists getting started",
                    price_monthly=0.0,
                    price_yearly=0.0,
                    monthly_quota=5,
                    max_file_size=10 * 1024 * 1024,
                    ai_analysis_enabled=False,
                    priority_support=False,
                    api_access=False,
                    team_members=1
                ),
                SubscriptionPlan(
                    name="basic",
                    display_name="Basic",
                    description="For serious drone enthusiasts",
                    price_monthly=9.99,
                    price_yearly=99.0,
                    monthly_quota=25,
                    max_file_size=50 * 1024 * 1024,
                    ai_analysis_enabled=True,
                    priority_support=False,
                    api_access=False,
                    team_members=1
                ),
                SubscriptionPlan(
                    name="pro",
                    display_name="Pro",
                    description="For professional pilots and small teams",
                    price_monthly=29.99,
                    price_yearly=299.0,
                    monthly_quota=100,
                    max_file_size=100 * 1024 * 1024,
                    ai_analysis_enabled=True,
                    priority_support=True,
                    api_access=True,
                    team_members=3
                ),
                SubscriptionPlan(
                    name="enterprise",
                    display_name="Enterprise",
                    description="For organizations with advanced needs",
                    price_monthly=99.99,
                    price_yearly=999.0,
                    monthly_quota=500,
                    max_file_size=500 * 1024 * 1024,
                    ai_analysis_enabled=True,
                    priority_support=True,
                    api_access=True,
                    team_members=10
                )
            ]
            for plan in default_plans:
                db.add(plan)
            db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error initializing plans: {e}")
    finally:
        db.close()


# Export models for easy importing
__all__ = [
    'User',
    'FlightLog',
    'FlightAnalysis',
    'SubscriptionPlan',
    'TuningBackup',
    'TuningSession',
    'Base',
    'engine',
    'SessionLocal',
    'get_db',
    'init_db'
]
