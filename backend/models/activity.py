from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.database import Base
from datetime import datetime


class TeamActivityLog(Base):
    __tablename__ = "team_activity_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String(50), nullable=False)  # MEMBER_JOINED, MEMBER_LEFT, MEMBER_KICKED, ROLE_CHANGED, PROJECT_CREATED, etc.
    target_type = Column(String(50))  # USER, PROJECT, TEAM
    target_id = Column(Integer)
    target_name = Column(String(200))
    details = Column(Text)  # JSON string with additional info
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    team = relationship("Team", back_populates="activity_logs")
    user = relationship("User")


class IssueHistory(Base):
    __tablename__ = "issue_histories"
    
    id = Column(Integer, primary_key=True, index=True)
    issue_id = Column(Integer, ForeignKey("issues.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    field = Column(String(50), nullable=False)  # status, priority, assignee, title, due_date
    old_value = Column(String(500))
    new_value = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    issue = relationship("Issue", back_populates="history")
    user = relationship("User")
