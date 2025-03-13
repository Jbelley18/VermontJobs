from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from .database import Base

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    company = Column(String, index=True)
    location = Column(String, index=True)
    description = Column(Text)
    salary_min = Column(Float, nullable=True)
    salary_max = Column(Float, nullable=True)
    url = Column(String, unique=True, index=True)
    posted_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    source = Column(String, index=True)  # e.g., "indeed", "linkedin", "vtjobs"
    is_remote = Column(Boolean, default=False)
    
    # Relationship with tags
    tags = relationship("JobTag", back_populates="job")


class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    
    # Relationship with jobs
    jobs = relationship("JobTag", back_populates="tag")


class JobTag(Base):
    __tablename__ = "job_tags"

    job_id = Column(Integer, ForeignKey("jobs.id"), primary_key=True)
    tag_id = Column(Integer, ForeignKey("tags.id"), primary_key=True)
    
    # Relationships
    job = relationship("Job", back_populates="tags")
    tag = relationship("Tag", back_populates="jobs")