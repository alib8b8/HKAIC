"""
HKAIC SaaS - Database Models
Compatibility module - imports from database.py
"""

# Re-export models from database module for compatibility
from app.database import (
    User,
    FlightLog,
    FlightAnalysis,
    SubscriptionPlan,
    TuningBackup,
    TuningSession,
    Base
)

__all__ = [
    'User',
    'FlightLog',
    'FlightAnalysis',
    'SubscriptionPlan',
    'TuningBackup',
    'TuningSession',
    'Base'
]
