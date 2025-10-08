# database/db_manager.py
"""
Database Manager Implementation
Handles all database operations.
"""

try:
    from sqlalchemy import create_engine, func
    from sqlalchemy.orm import sessionmaker
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False

from datetime import datetime, timedelta
from typing import Optional, List, Dict
import streamlit as st
import json

# Import models only if SQLAlchemy is available
if SQLALCHEMY_AVAILABLE:
    from database.models import Base, User, Session, APIUsage, UserActivity, QuotaHistory

class DatabaseManager:
    """Singleton database manager."""
    
    _instance = None
    
    def __new__(cls, db_path: str = "database/users.db"):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            
            if SQLALCHEMY_AVAILABLE:
                cls._instance.engine = create_engine(f'sqlite:///{db_path}', echo=False)
                Base.metadata.create_all(cls._instance.engine)
                cls._instance.SessionLocal = sessionmaker(bind=cls._instance.engine)
            else:
                cls._instance.engine = None
                cls._instance.SessionLocal = None
                
        return cls._instance
    
    def get_db(self):
        """Get database session."""
        if not SQLALCHEMY_AVAILABLE or not self.SessionLocal:
            return None
        return self.SessionLocal()
    
    # ========== USER OPERATIONS ==========
    
    def create_or_update_user(self, user_info: Dict):
        """Create new user or update existing."""
        if not SQLALCHEMY_AVAILABLE:
            # Fallback: return user info without database persistence
            return {
                'id': 1,
                'email': user_info['email'],
                'name': user_info['name'],
                'google_id': user_info['google_id'],
                'picture_url': user_info.get('picture'),
                'last_login': datetime.now()
            }
        
        db = self.get_db()
        if not db:
            return None
            
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
    
    def get_user_by_email(self, email: str):
        """Get user by email."""
        if not SQLALCHEMY_AVAILABLE:
            return None
            
        db = self.get_db()
        if not db:
            return None
            
        try:
            return db.query(User).filter(User.email == email).first()
        finally:
            db.close()
    
    # ========== SESSION OPERATIONS ==========
    
    def create_session(self, user_email: str, session_id: str, expires_at: datetime):
        """Create new session."""
        if not SQLALCHEMY_AVAILABLE:
            # Fallback: return session info without database persistence
            return {
                'id': 1,
                'session_id': session_id,
                'user_email': user_email,
                'expires_at': expires_at,
                'is_active': True
            }
        
        db = self.get_db()
        if not db:
            return None
            
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
        if not SQLALCHEMY_AVAILABLE:
            # Fallback: do nothing, just return
            return
        
        db = self.get_db()
        if not db:
            return
            
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
        if not SQLALCHEMY_AVAILABLE:
            # Fallback: do nothing, just return
            return
        
        db = self.get_db()
        if not db:
            return
            
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
