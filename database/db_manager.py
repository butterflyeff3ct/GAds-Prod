# database/db_manager.py
"""
Database Manager Implementation
Handles all database operations.
"""

from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import streamlit as st
import json

# Import models
from database.models import Base, User, Session, APIUsage, UserActivity, QuotaHistory

class DatabaseManager:
    """Singleton database manager."""
    
    _instance = None
    
    def __new__(cls, db_path: str = "database/users.db"):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance.engine = create_engine(f'sqlite:///{db_path}', echo=False)
            Base.metadata.create_all(cls._instance.engine)
            cls._instance.SessionLocal = sessionmaker(bind=cls._instance.engine)
        return cls._instance
    
    def get_db(self):
        """Get database session."""
        return self.SessionLocal()
    
    # ========== USER OPERATIONS ==========
    
    def create_or_update_user(self, user_info: Dict) -> User:
        """Create new user or update existing."""
        db = self.get_db()
        try:
            user = db.query(User).filter(User.email == user_info['email']).first()
            
            if user:
                user.name = user_info['name']
                user.picture_url = user_info.get('picture')
                user.last_login = datetime.now()
            else:
                user = User(
                    email=user_info['email'],
                    name=user_info['name'],
                    google_id=user_info['google_id'],
                    picture_url=user_info.get('picture'),
                    last_login=datetime.now()
                )
                db.add(user)
            
            db.commit()
            db.refresh(user)
            return user
        finally:
            db.close()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        db = self.get_db()
        try:
            return db.query(User).filter(User.email == email).first()
        finally:
            db.close()
    
    # ========== SESSION OPERATIONS ==========
    
    def create_session(self, user_email: str, session_id: str, expires_at: datetime) -> Session:
        """Create new session."""
        db = self.get_db()
        try:
            user = db.query(User).filter(User.email == user_email).first()
            if not user:
                return None
            
            session = Session(
                session_id=session_id,
                user_id=user.id,
                expires_at=expires_at,
                is_active=True
            )
            db.add(session)
            db.commit()
            db.refresh(session)
            return session
        finally:
            db.close()
    
    # ========== API USAGE TRACKING ==========
    
    def record_api_usage(self, user_email: str, api_name: str, success: bool = True):
        """Record an API call."""
        db = self.get_db()
        try:
            user = db.query(User).filter(User.email == user_email).first()
            if not user:
                return
            
            hour_bucket = datetime.now().replace(minute=0, second=0, microsecond=0)
            
            usage = APIUsage(
                user_id=user.id,
                api_name=api_name,
                hour_bucket=hour_bucket,
                success=success
            )
            db.add(usage)
            db.commit()
        finally:
            db.close()
    
    # ========== ACTIVITY LOGGING ==========
    
    def log_activity(self, user_email: str, activity_type: str, details: Dict = None):
        """Log user activity."""
        db = self.get_db()
        try:
            user = db.query(User).filter(User.email == user_email).first()
            if not user:
                return
            
            activity = UserActivity(
                user_id=user.id,
                activity_type=activity_type,
                details=json.dumps(details) if details else None
            )
            db.add(activity)
            db.commit()
        finally:
            db.close()

@st.cache_resource
def get_database_manager():
    """Get cached database manager instance."""
    return DatabaseManager()
