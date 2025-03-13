import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session
from app.main import run_scrapers
from app import schemas

@patch('app.main.indeed_scraper')
def test_run_scrapers(mock_indeed_scraper, db):
    """Test the background scraping functionality."""
    # Create mock job data
    mock_job_data = {
        "title": "Test Job",
        "company": "Test Company",
        "location": "Burlington, VT",
        "description": "This is a test job description",
        "url": "https://example.com/job1",
        "source": "indeed",
        "is_remote": False,
        "salary_min": 60000.0,
        "salary_max": 80000.0,
        "posted_date": None
    }
    
    # Mock the search and get_job_details methods
    mock_indeed_scraper.search.return_value = [mock_job_data]
    mock_indeed_scraper.get_job_details.return_value = {
        "description": "Detailed job description with python and javascript requirements."
    }
    
    # Run the scraper
    run_scrapers(db)
    
    # Verify that search was called for each keyword
    assert mock_indeed_scraper.search.call_count == 4  # Four keywords in the function
    
    # Verify a job was added to the database
    jobs = db.query(schemas.Job).all()
    assert len(jobs) >= 1
    
    # Check that tags were created
    tags = db.query(schemas.Tag).all()
    assert len(tags) > 0
    
    # Check that job-tag associations were created
    job_tags = db.query(schemas.JobTag).all()
    assert len(job_tags) > 0

@patch('app.main.indeed_scraper')
def test_run_scrapers_existing_job(mock_indeed_scraper, db):
    """Test that run_scrapers doesn't duplicate existing jobs."""
    # First, add a job to the database
    existing_job = schemas.Job(
        title="Existing Job",
        company="Existing Company",
        location="Vermont",
        description="Existing description",
        url="https://example.com/existing-job",
        source="indeed",
        is_remote=False
    )
    db.add(existing_job)
    db.commit()
    
    # Create mock job data with the same URL
    mock_job_data = {
        "title": "Updated Job",  # Different title
        "company": "Updated Company",
        "location": "Burlington, VT",
        "description": "Updated description",
        "url": "https://example.com/existing-job",  # Same URL
        "source": "indeed",
        "is_remote": False,
        "salary_min": 70000.0,
        "salary_max": 90000.0,
        "posted_date": None
    }
    
    # Mock the search method
    mock_indeed_scraper.search.return_value = [mock_job_data]
    
    # Run the scraper
    run_scrapers(db)
    
    # Verify that the job wasn't duplicated
    jobs = db.query(schemas.Job).all()
    assert len(jobs) == 1
    
    # Verify the job still has its original title (wasn't updated)
    job = db.query(schemas.Job).first()
    assert job.title == "Existing Job"