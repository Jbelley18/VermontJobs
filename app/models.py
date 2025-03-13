from pydantic import BaseModel, HttpUrl
from datetime import datetime
from typing import List, Optional, Union, Any

# Tag Models
class TagBase(BaseModel):
    name: str

class TagCreate(TagBase):
    pass

class Tag(TagBase):
    id: int

    class Config:
        from_attributes = True

# Job Models
class JobBase(BaseModel):
    title: str
    company: str
    location: str
    description: str
    url: str
    source: str
    is_remote: bool = False
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    posted_date: Optional[datetime] = None

class JobCreate(JobBase):
    pass

class JobUpdate(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    source: Optional[str] = None
    is_remote: Optional[bool] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    posted_date: Optional[datetime] = None

class Job(JobBase):
    id: int
    created_at: datetime
    updated_at: datetime
    tags: List[Tag] = []

    class Config:
        from_attributes = True

# JobSearch Model for filtering jobs
class JobSearch(BaseModel):
    keyword: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    source: Optional[str] = None
    is_remote: Optional[bool] = None
    min_salary: Optional[float] = None
    max_salary: Optional[float] = None
    tags: Optional[List[str]] = None
    posted_after: Optional[datetime] = None
    posted_before: Optional[datetime] = None