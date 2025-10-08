# database/models.py
"""
Database Models
SQLAlchemy models for users, sessions, and quota tracking.
"""

try:
    from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, func
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import relationship
    SQLALCHEMY_AVAILABLE = True
    Base = declarative_base()
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    Base = None

from datetime import datetime

if SQLALCHEMY_AVAILABLE and Base:
    class User(Base):
        """User account model."""
        __tablename__ = 'users'
        
        id = Column(Integer, primary_key=True)
        email = Column(String(255), unique=True, nullable=False, index=True)
        name = Column(String(255))
        google_id = Column(String(255), unique=True)
        picture_url = Column(String(512))
        is_admin = Column(Boolean, default=False)
        is_active = Column(Boolean, default=True)
        created_at = Column(DateTime, default=datetime.now)
        last_login = Column(DateTime)
        
        # Relationships
        sessions = relationship("Session", back_populates="user")
        api_usage = relationship("APIUsage", back_populates="user")
        activities = relationship("UserActivity", back_populates="user")
        
        def __repr__(self):
            return f"<User(email='{self.email}', name='{self.name}')>"

    class Session(Base):
        """User session model."""
        __tablename__ = 'sessions'
        
        id = Column(Integer, primary_key=True)
        session_id = Column(String(255), unique=True, nullable=False, index=True)
        user_id = Column(Integer, ForeignKey('users.id'))
        created_at = Column(DateTime, default=datetime.now)
        last_activity = Column(DateTime, default=datetime.now)
        expires_at = Column(DateTime)
        is_active = Column(Boolean, default=True)
        ip_address = Column(String(45))
        user_agent = Column(String(512))
        
        # Relationship
        user = relationship("User", back_populates="sessions")
        
        def __repr__(self):
            return f"<Session(session_id='{self.session_id}', user_id={self.user_id})>"

    class APIUsage(Base):
        """API usage tracking model."""
        __tablename__ = 'api_usage'
        
        id = Column(Integer, primary_key=True)
        user_id = Column(Integer, ForeignKey('users.id'))
        api_name = Column(String(100), nullable=False, index=True)
        timestamp = Column(DateTime, default=datetime.now, index=True)
        hour_bucket = Column(DateTime, index=True)
        count = Column(Integer, default=1)
        endpoint = Column(String(255))
        success = Column(Boolean, default=True)
        error_message = Column(Text)
        
        # Relationship
        user = relationship("User", back_populates="api_usage")
        
        def __repr__(self):
            return f"<APIUsage(user_id={self.user_id}, api='{self.api_name}', count={self.count})>"

    class UserActivity(Base):
        """User activity log model."""
        __tablename__ = 'user_activity'
        
        id = Column(Integer, primary_key=True)
        user_id = Column(Integer, ForeignKey('users.id'))
        activity_type = Column(String(100), nullable=False, index=True)
        activity_name = Column(String(255))
        timestamp = Column(DateTime, default=datetime.now, index=True)
        details = Column(Text)
        session_id = Column(String(255))
        
        # Relationship
        user = relationship("User", back_populates="activities")
        
        def __repr__(self):
            return f"<UserActivity(user_id={self.user_id}, type='{self.activity_type}')>"

    class QuotaHistory(Base):
        """Historical quota usage for analytics."""
        __tablename__ = 'quota_history'
        
        id = Column(Integer, primary_key=True)
        user_id = Column(Integer, ForeignKey('users.id'))
        date = Column(DateTime, index=True)
        api_name = Column(String(100))
        total_calls = Column(Integer)
        peak_hour_calls = Column(Integer)
        
        def __repr__(self):
            return f"<QuotaHistory(user_id={self.user_id}, api='{self.api_name}', calls={self.total_calls})>"
else:
    # Fallback classes when SQLAlchemy is not available
    class User:
        pass
    
    class Session:
        pass
    
    class APIUsage:
        pass
    
    class UserActivity:
        pass
    
    class QuotaHistory:
        pass
