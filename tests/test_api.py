import pytest
from fastapi.testclient import TestClient
from app.main import app

def test_root_endpoint(client):
    """Test the root endpoint returns the expected information."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert "documentation" in data
    assert data["message"] == "Vermont Jobs API"

def test_get_jobs_empty(client):
    """Test getting jobs when the database is empty."""
    response = client.get("/jobs")
    assert response.status_code == 200
    assert response.json() == []

def test_get_jobs(client, test_jobs):
    """Test getting all jobs."""
    response = client.get("/jobs")
    assert response.status_code == 200
    jobs = response.json()
    assert len(jobs) == 3
    
    # Check the first job's properties
    assert jobs[0]["title"] == "Python Developer"
    assert jobs[0]["company"] == "TechCorp"
    assert jobs[0]["is_remote"] is False

def test_get_jobs_with_filter(client, test_jobs):
    """Test filtering jobs by various parameters."""
    # Filter by keyword (title)
    response = client.get("/jobs?keyword=Python")
    assert response.status_code == 200
    jobs = response.json()
    assert len(jobs) == 1
    assert jobs[0]["title"] == "Python Developer"
    
    # Filter by company
    response = client.get("/jobs?company=WebWorks")
    assert response.status_code == 200
    jobs = response.json()
    assert len(jobs) == 1
    assert jobs[0]["company"] == "WebWorks"
    
    # Filter by remote status
    response = client.get("/jobs?is_remote=true")
    assert response.status_code == 200
    jobs = response.json()
    assert len(jobs) == 1
    assert jobs[0]["is_remote"] is True
    assert jobs[0]["title"] == "Remote Frontend Developer"
    
    # Filter by minimum salary
    response = client.get("/jobs?min_salary=75000")
    assert response.status_code == 200
    jobs = response.json()
    assert len(jobs) == 2
    assert all(job["salary_min"] >= 75000 for job in jobs)

def test_get_job_by_id(client, test_jobs):
    """Test getting a specific job by ID."""
    # Existing job
    response = client.get("/jobs/1")
    assert response.status_code == 200
    job = response.json()
    assert job["id"] == 1
    assert job["title"] == "Python Developer"
    
    # Non-existent job
    response = client.get("/jobs/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Job not found"

def test_get_tags(client, test_jobs):
    """Test getting all tags."""
    response = client.get("/tags")
    assert response.status_code == 200
    tags = response.json()
    assert len(tags) == 3
    assert {"id": 1, "name": "python"} in tags
    assert {"id": 2, "name": "react"} in tags
    assert {"id": 3, "name": "data-analysis"} in tags

def test_get_stats(client, test_jobs):
    """Test getting job statistics."""
    response = client.get("/stats")
    assert response.status_code == 200
    stats = response.json()
    
    assert stats["total_jobs"] == 3
    assert stats["remote_jobs"] == 1
    assert stats["onsite_jobs"] == 2
    
    # Check job sources
    assert "indeed" in stats["jobs_by_source"]
    assert "linkedin" in stats["jobs_by_source"]
    assert "vtjobs" in stats["jobs_by_source"]
    assert stats["jobs_by_source"]["indeed"] == 1