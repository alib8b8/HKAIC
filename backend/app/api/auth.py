"""
User Authentication & User Management API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
from uuid import uuid4
import uuid
import re
import logging
from app.database import get_db
from app.models import User, SubscriptionPlan
from app.schemas import (
    UserCreate, UserLogin, UserResponse, Token, 
    MessageResponse, SubscriptionPlanResponse
)
from app.auth import (
    verify_password, get_password_hash, create_access_token,
    get_current_user
)
from app.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


def validate_password_strength(password: str):
    """
    Validate password strength
    Returns None if valid, raises HTTPException if invalid
    """
    if len(password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long"
        )
    if not re.search(r'[A-Z]', password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least one uppercase letter"
        )
    if not re.search(r'[a-z]', password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least one lowercase letter"
        )
    if not re.search(r'[0-9]', password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least one number"
        )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user account"""
    # Validate password strength
    validate_password_strength(user_data.password)
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Generate unique tenant ID
    tenant_id = str(uuid.uuid4())
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=hashed_password,
        tenant_id=tenant_id,
        subscription_tier="free",
        monthly_quota=5,
        used_quota=0
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user


@router.post("/login", response_model=Token)
async def login(login_data: UserLogin, db: Session = Depends(get_db)):
    """Login to get access token"""
    user = db.query(User).filter(User.email == login_data.email).first()
    
    # Check password
    if not user or not verify_password(login_data.password, user.hashed_password):
        logger.warning(f"Failed login attempt for email: {login_data.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        logger.warning(f"Login attempt for inactive account: {login_data.email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive account"
        )
    
    # Successful login
    logger.info(f"User logged in: {user.email} (ID: {user.id})")
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user profile"""
    return current_user


# Subscription Plan API
subscription_router = APIRouter(prefix="/api/subscription", tags=["Subscription"])


@subscription_router.get("/plans", response_model=list[SubscriptionPlanResponse])
async def get_subscription_plans(db: Session = Depends(get_db)):
    """Get all available subscription plans"""
    plans = db.query(SubscriptionPlan).filter(SubscriptionPlan.is_active == True).all()
    return plans


@subscription_router.get("/my-plan")
async def get_user_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's subscription plan"""
    plan = db.query(SubscriptionPlan).filter(
        SubscriptionPlan.name == current_user.subscription_tier).first()
    
    return {
        "plan": plan,
        "quota_used": current_user.used_quota,
        "quota_total": current_user.monthly_quota,
        "expires_at": current_user.subscription_expires_at
    }
