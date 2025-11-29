from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Date, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base
import enum


class IssuePriority(str, enum.Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class Issue(Base):
    __tablename__ = "issues"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(30), default="Backlog")
    priority = Column(SQLEnum(IssuePriority), default=IssuePriority.MEDIUM)
    assignee_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    due_date = Column(Date, nullable=True)
    position = Column(Integer, default=0)
    ai_summary = Column(Text, nullable=True)
    ai_summary_cached_at = Column(DateTime, nullable=True)
    ai_suggestion = Column(Text, nullable=True)
    ai_suggestion_cached_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    
    # Relationships
    project = relationship("Project", back_populates="issues")
    owner = relationship("User", back_populates="owned_issues", foreign_keys=[owner_id])
    assignee = relationship("User", back_populates="assigned_issues", foreign_keys=[assignee_id])
    comments = relationship("Comment", back_populates="issue")
    issue_labels = relationship("IssueLabel", back_populates="issue")
    history = relationship("IssueHistory", back_populates="issue")


class Label(Base):
    __tablename__ = "labels"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    name = Column(String(30), nullable=False)
    color = Column(String(7), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="labels")
    issue_labels = relationship("IssueLabel", back_populates="label")


class IssueLabel(Base):
    __tablename__ = "issue_labels"
    
    id = Column(Integer, primary_key=True, index=True)
    issue_id = Column(Integer, ForeignKey("issues.id"), nullable=False)
    label_id = Column(Integer, ForeignKey("labels.id"), nullable=False)
    
    # Relationships
    issue = relationship("Issue", back_populates="issue_labels")
    label = relationship("Label", back_populates="issue_labels")


class Comment(Base):
    __tablename__ = "comments"
    
    id = Column(Integer, primary_key=True, index=True)
    issue_id = Column(Integer, ForeignKey("issues.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    
    # Relationships
    issue = relationship("Issue", back_populates="comments")
    user = relationship("User", back_populates="comments")
