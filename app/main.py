from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import List, Optional
from datetime import datetime, timedelta

from . import models, schemas
from .database import engine, get_db
from .scraper.indeed import IndeedScraper
# You would import other scrapers similarly
# from .scraper.linkedin import LinkedInScraper
# from .scraper.vtjobs import VTJobsScraper

# Create tables in the database
schemas.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Vermont Jobs API",
    description="API for tracking job listings across various sources in Vermont",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize scrapers
indeed_scraper = IndeedScraper()
# linkedin_scraper = LinkedInScraper()
# vtjobs_scraper = VTJobsScraper()

# Background task to run scrapers and update the database
def run_scrapers(db: Session):
    """Run all scrapers and update the database with new job listings."""
    keywords = ["software developer", "data analyst", "web developer", "engineer"]
    
    for keyword in keywords:
        # Run Indeed scraper
        indeed_jobs = indeed_scraper.search(keyword)
        for job_data in indeed_jobs:
            # Check if job already exists by URL
            existing_job = db.query(schemas.Job).filter(schemas.Job.url == job_data["url"]).first()
            
            if not existing_job:
                # Get full job details (description)
                if "url" in job_data and job_data["url"]:
                    details = indeed_scraper.get_job_details(job_data["url"])
                    job_data["description"] = details.get("description", job_data.get("description", ""))
                
                # Create new job record
                new_job = schemas.Job(**job_data)
                db.add(new_job)
                db.commit()
                db.refresh(new_job)
                
                # Extract and add tags (this would be more sophisticated in production)
                keywords_to_check = ["python", "javascript", "react", "sql", "remote", "junior", "senior"]
                for keyword in keywords_to_check:
                    if keyword.lower() in job_data["title"].lower() or keyword.lower() in job_data.get("description", "").lower():
                        # Check if tag exists
                        tag = db.query(schemas.Tag).filter(schemas.Tag.name == keyword).first()
                        if not tag:
                            tag = schemas.Tag(name=keyword)
                            db.add(tag)
                            db.commit()
                            db.refresh(tag)
                        
                        # Add relationship
                        job_tag = schemas.JobTag(job_id=new_job.id, tag_id=tag.id)
                        db.add(job_tag)
                        db.commit()
        
        # Add similar blocks for other scrapers
        # linkedin_jobs = linkedin_scraper.search(keyword)
        # vtjobs_jobs = vtjobs_scraper.search(keyword)

# API Routes
@app.get("/", tags=["General"])
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Vermont Jobs API",
        "version": "0.1.0",
        "documentation": "/docs",
    }

@app.post("/jobs/scrape", tags=["Admin"])
async def scrape_jobs(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Trigger a job scraping run (admin endpoint)."""
    background_tasks.add_task(run_scrapers, db)
    return {"message": "Job scraping started in the background"}

@app.get("/jobs", response_model=List[models.Job], tags=["Jobs"])
async def get_jobs(
    keyword: Optional[str] = None,
    company: Optional[str] = None,
    location: Optional[str] = None,
    is_remote: Optional[bool] = None,
    min_salary: Optional[float] = None,
    tag: Optional[str] = None,
    days: Optional[int] = None,
    skip: int = 0, 
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get all jobs with optional filtering.
    
    - **keyword**: Search in job title and description
    - **company**: Filter by company name
    - **location**: Filter by job location
    - **is_remote**: Filter for remote jobs
    - **min_salary**: Filter by minimum salary
    - **tag**: Filter by job tag
    - **days**: Filter for jobs posted within last X days
    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return (pagination)
    """
    query = db.query(schemas.Job)
    
    # Apply filters
    if keyword:
        query = query.filter(or_(
            schemas.Job.title.ilike(f"%{keyword}%"),
            schemas.Job.description.ilike(f"%{keyword}%")
        ))
    
    if company:
        query = query.filter(schemas.Job.company.ilike(f"%{company}%"))
    
    if location:
        query = query.filter(schemas.Job.location.ilike(f"%{location}%"))
    
    if is_remote is not None:
        query = query.filter(schemas.Job.is_remote == is_remote)
    
    if min_salary:
        query = query.filter(schemas.Job.salary_min >= min_salary)
    
    if tag:
        query = query.join(schemas.JobTag).join(schemas.Tag).filter(schemas.Tag.name == tag)
    
    if days:
        date_threshold = datetime.utcnow() - timedelta(days=days)
        query = query.filter(schemas.Job.posted_date >= date_threshold)
    
    # Apply pagination
    jobs = query.order_by(schemas.Job.posted_date.desc()).offset(skip).limit(limit).all()
    
    return jobs

@app.get("/jobs/{job_id}", response_model=models.Job, tags=["Jobs"])
async def get_job(job_id: int, db: Session = Depends(get_db)):
    """Get a specific job by ID."""
    job = db.query(schemas.Job).filter(schemas.Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@app.get("/tags", response_model=List[models.Tag], tags=["Tags"])
async def get_tags(db: Session = Depends(get_db)):
    """Get all available job tags."""
    tags = db.query(schemas.Tag).all()
    return tags

@app.get("/stats", tags=["Stats"])
async def get_stats(db: Session = Depends(get_db)):
    """Get job statistics."""
    # Total job count
    total_jobs = db.query(schemas.Job).count()
    
    # Jobs by source
    jobs_by_source = db.query(
        schemas.Job.source, 
        db.func.count(schemas.Job.id)
    ).group_by(schemas.Job.source).all()
    
    # Remote vs. on-site jobs
    remote_jobs = db.query(schemas.Job).filter(schemas.Job.is_remote == True).count()
    onsite_jobs = total_jobs - remote_jobs
    
    # Jobs posted in the last week
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_jobs = db.query(schemas.Job).filter(schemas.Job.posted_date >= week_ago).count()
    
    # Top companies by job count
    top_companies = db.query(
        schemas.Job.company, 
        db.func.count(schemas.Job.id)
    ).group_by(schemas.Job.company).order_by(db.func.count(schemas.Job.id).desc()).limit(10).all()
    
    # Popular tags
    popular_tags = db.query(
        schemas.Tag.name, 
        db.func.count(schemas.JobTag.job_id)
    ).join(schemas.JobTag).group_by(schemas.Tag.name).order_by(db.func.count(schemas.JobTag.job_id).desc()).limit(10).all()
    
    return {
        "total_jobs": total_jobs,
        "jobs_by_source": dict(jobs_by_source),
        "remote_jobs": remote_jobs,
        "onsite_jobs": onsite_jobs,
        "recent_jobs": recent_jobs,
        "top_companies": dict(top_companies),
        "popular_tags": dict(popular_tags)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)