import requests
from bs4 import BeautifulSoup
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
import re
import time

logger = logging.getLogger(__name__)

class IndeedScraper:
    """Scraper for Indeed job listings in Vermont"""
    
    BASE_URL = "https://www.indeed.com/jobs"
    SOURCE_NAME = "indeed"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        })
    
    def _parse_salary(self, salary_text: str) -> Dict[str, Optional[float]]:
        """Parse salary information from job listing."""
        if not salary_text:
            return {"salary_min": None, "salary_max": None}
        
        # Handle different salary formats
        # Example patterns: "$50,000 - $70,000 a year", "$20 an hour"
        salary_text = salary_text.lower()
        
        # Yearly salary range
        range_match = re.search(r'\$(\d+[,\d]*)\s*-\s*\$(\d+[,\d]*)\s*a\s*year', salary_text)
        if range_match:
            min_salary = float(range_match.group(1).replace(',', ''))
            max_salary = float(range_match.group(2).replace(',', ''))
            return {"salary_min": min_salary, "salary_max": max_salary}
        
        # Single yearly salary
        single_year_match = re.search(r'\$(\d+[,\d]*)\s*a\s*year', salary_text)
        if single_year_match:
            salary = float(single_year_match.group(1).replace(',', ''))
            return {"salary_min": salary, "salary_max": salary}
        
        # Hourly rate
        hourly_match = re.search(r'\$(\d+[,.\d]*)\s*an\s*hour', salary_text)
        if hourly_match:
            hourly_rate = float(hourly_match.group(1).replace(',', ''))
            # Convert to yearly (40 hours/week, 52 weeks/year)
            yearly = hourly_rate * 40 * 52
            return {"salary_min": yearly, "salary_max": yearly}
        
        return {"salary_min": None, "salary_max": None}
    
    def _parse_date(self, date_text: str) -> Optional[datetime]:
        """Parse posting date from job listing."""
        if not date_text:
            return None
        
        # Handle common date formats
        date_text = date_text.lower().strip()
        
        # Posted today
        if "today" in date_text or "just posted" in date_text:
            return datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Posted X days ago
        days_ago_match = re.search(r'(\d+) days? ago', date_text)
        if days_ago_match:
            days = int(days_ago_match.group(1))
            date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            # Subtract days
            from datetime import timedelta
            return date - timedelta(days=days)
        
        # Posted X hours ago
        hours_ago_match = re.search(r'(\d+) hours? ago', date_text)
        if hours_ago_match:
            return datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Other formats could be added as needed
        
        return None
    
    def search(self, keywords: str = "", location: str = "Vermont") -> List[Dict[str, Any]]:
        """
        Search Indeed for jobs matching the criteria.
        
        Args:
            keywords: Job search keywords
            location: Job location (default: Vermont)
            
        Returns:
            List of job listings
        """
        params = {
            "q": keywords,
            "l": location,
            "sort": "date"
        }
        
        url = f"{self.BASE_URL}"
        jobs = []
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            job_listings = soup.select("div.job_seen_beacon")
            
            for job in job_listings:
                try:
                    # Extract job data
                    title_elem = job.select_one("h2.jobTitle span")
                    company_elem = job.select_one("span.companyName")
                    location_elem = job.select_one("div.companyLocation")
                    salary_elem = job.select_one("span.salary-snippet")
                    date_elem = job.select_one("span.date")
                    
                    # Get URL
                    job_id = job.get("data-jk", "")
                    job_url = f"https://www.indeed.com/viewjob?jk={job_id}" if job_id else None
                    
                    # Check for remote
                    is_remote = False
                    if location_elem and "remote" in location_elem.text.lower():
                        is_remote = True
                    
                    # Create job object
                    job_data = {
                        "title": title_elem.text.strip() if title_elem else "Unknown Title",
                        "company": company_elem.text.strip() if company_elem else "Unknown Company",
                        "location": location_elem.text.strip() if location_elem else "Unknown Location",
                        "url": job_url,
                        "source": self.SOURCE_NAME,
                        "is_remote": is_remote,
                        "posted_date": self._parse_date(date_elem.text if date_elem else ""),
                    }
                    
                    # Parse salary if available
                    if salary_elem:
                        salary_data = self._parse_salary(salary_elem.text)
                        job_data.update(salary_data)
                    else:
                        job_data.update({"salary_min": None, "salary_max": None})
                    
                    # Attempt to get job description
                    # This would typically require visiting the job detail page
                    # For simplicity, we'll just use a placeholder here
                    job_data["description"] = "Full description requires visiting the job page."
                    
                    jobs.append(job_data)
                    
                except Exception as e:
                    logger.error(f"Error parsing job listing: {e}")
                    continue
                    
            return jobs
            
        except requests.RequestException as e:
            logger.error(f"Error fetching Indeed jobs: {e}")
            return []

    def get_job_details(self, job_url: str) -> Dict[str, Any]:
        """
        Get detailed information for a specific job.
        
        Args:
            job_url: URL of the job listing
            
        Returns:
            Dictionary with detailed job information
        """
        try:
            # Add a delay to avoid getting blocked
            time.sleep(1)
            
            response = self.session.get(job_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Extract job description
            description_elem = soup.select_one("div#jobDescriptionText")
            description = description_elem.text.strip() if description_elem else "No description available."
            
            return {"description": description}
            
        except requests.RequestException as e:
            logger.error(f"Error fetching job details: {e}")
            return {"description": "Failed to retrieve job description."}

# Usage example:
if __name__ == "__main__":
    scraper = IndeedScraper()
    jobs = scraper.search("software developer")
    for job in jobs:
        print(f"{job['title']} - {job['company']} - {job['location']}")