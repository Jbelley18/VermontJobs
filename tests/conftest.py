import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from app.database import Base, get_db
from app.main import app
from app import schemas
import os

# Use in-memory SQLite database for testing
TEST_DATABASE_URL = "sqlite:///./test.db"

# Create test engine and session
engine = create_engine(
    TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db():
    # Create the database tables
    Base.metadata.create_all(bind=engine)
    
    # Create a session for testing
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Drop tables after test is complete
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db):
    # Override the dependency to use the test database
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def test_jobs(db):
    """Create some test job entries in the database"""
    jobs = [
        schemas.Job(
            title="Python Developer",
            company="TechCorp",
            location="Burlington, VT",
            description="Looking for a Python developer...",
            salary_min=70000.0,
            salary_max=90000.0,
            url="https://example.com/job1",
            source="indeed",
            is_remote=False
        ),
        schemas.Job(
            title="Remote Frontend Developer",
            company="WebWorks",
            location="Vermont",
            description="Frontend developer with React experience...",
            salary_min=80000.0,
            salary_max=100000.0,
            url="https://example.com/job2",
            source="linkedin",
            is_remote=True
        ),
        schemas.Job(
            title="Data Analyst",
            company="DataVT",
            location="Montpelier, VT",
            description="Analyzing data for Vermont businesses...",
            salary_min=65000.0,
            salary_max=75000.0,
            url="https://example.com/job3",
            source="vtjobs",
            is_remote=False
        )
    ]
    
    for job in jobs:
        db.add(job)
    
    # Add some tags
    tags = [
        schemas.Tag(name="python"),
        schemas.Tag(name="react"),
        schemas.Tag(name="data-analysis")
    ]
    
    for tag in tags:
        db.add(tag)
    
    db.commit()
    
    # Associate tags with jobs
    job_tags = [
        schemas.JobTag(job_id=1, tag_id=1),  # Python Developer - python
        schemas.JobTag(job_id=2, tag_id=2),  # Frontend Developer - react
        schemas.JobTag(job_id=3, tag_id=3)   # Data Analyst - data-analysis
    ]
    
    for job_tag in job_tags:
        db.add(job_tag)
    
    db.commit()
    
    # Return the test data for reference if needed
    return {
        "jobs": jobs,
        "tags": tags,
        "job_tags": job_tags
    }