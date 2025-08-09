"""
User service for user management
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from app.models import User, EmailLog
from app.schemas import UserCreate, UserUpdate


class UserService:
    def create_user(self, db: Session, user_data: UserCreate) -> User:
        """Create a new user"""
        user = User(
            email=user_data.email,
            name=user_data.name,
            is_active=True,
            email_verified=False
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return user
    
    def get_user_by_id(self, db: Session, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_email(self, db: Session, email: str) -> Optional[User]:
        """Get user by email"""
        return db.query(User).filter(User.email == email).first()
    
    def update_user(self, db: Session, user_id: int, user_data: UserUpdate) -> Optional[User]:
        """Update user information"""
        user = self.get_user_by_id(db, user_id)
        if not user:
            return None
        
        if user_data.name is not None:
            user.name = user_data.name
        if user_data.email is not None:
            user.email = user_data.email
        if user_data.is_active is not None:
            user.is_active = user_data.is_active
        
        db.commit()
        db.refresh(user)
        
        return user
    
    def verify_user_email(self, db: Session, user_id: int) -> bool:
        """Mark user email as verified"""
        user = self.get_user_by_id(db, user_id)
        if not user:
            return False
        
        user.email_verified = True
        db.commit()
        
        return True
    
    def log_email_sent(
        self, 
        db: Session, 
        user_id: int, 
        email_type: str, 
        subject: str, 
        content_preview: str, 
        status: str = "sent"
    ):
        """Log email delivery"""
        email_log = EmailLog(
            user_id=user_id,
            email_type=email_type,
            status=status,
            subject=subject,
            content_preview=content_preview[:200]
        )
        
        db.add(email_log)
        db.commit()
    
    def get_active_users(self, db: Session) -> List[User]:
        """Get all active users"""
        return db.query(User).filter(User.is_active == True).all()