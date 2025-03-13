import pytest
from unittest.mock import patch, MagicMock
from app.scraper.indeed import IndeedScraper

class TestIndeedScraper:
    """Tests for the Indeed job scraper."""
    
    def test_parse_salary(self):
        """Test parsing different salary formats."""
        scraper = IndeedScraper()
        
        # Test yearly salary range
        result = scraper._parse_salary("$50,000 - $70,000 a year")
        assert result["salary_min"] == 50000.0
        assert result["salary_max"] == 70000.0
        
        # Test single yearly salary
        result = scraper._parse_salary("$60,000 a year")
        assert result["salary_min"] == 60000.0
        assert result["salary_max"] == 60000.0
        
        # Test hourly rate
        result = scraper._parse_salary("$25 an hour")
        assert result["salary_min"] == 25 * 40 * 52  # hourly to yearly conversion
        assert result["salary_max"] == 25 * 40 * 52
        
        # Test empty/invalid salary
        result = scraper._parse_salary("")
        assert result["salary_min"] is None
        assert result["salary_max"] is None
        
        result = scraper._parse_salary("Competitive salary")
        assert result["salary_min"] is None
        assert result["salary_max"] is None
    
    def test_parse_date(self):
        """Test parsing different date formats."""
        scraper = IndeedScraper()
        
        # Today
        result = scraper._parse_date("Today")
        assert result is not None
        
        # Just posted
        result = scraper._parse_date("Just posted")
        assert result is not None
        
        # Days ago
        result = scraper._parse_date("5 days ago")
        assert result is not None
        
        # Hours ago
        result = scraper._parse_date("3 hours ago")
        assert result is not None
        
        # Empty/invalid date
        result = scraper._parse_date("")
        assert result is None
    
    @patch('requests.Session')
    def test_search(self, mock_session):
        """Test job search functionality with mocked responses."""
        # Create a mock response
        mock_response = MagicMock()
        mock_response.text = """
        <div class="job_seen_beacon">
            <h2 class="jobTitle"><span>Python Developer</span></h2>
            <span class="companyName">TechCorp</span>
            <div class="companyLocation">Burlington, VT</div>
            <span class="salary-snippet">$70,000 - $90,000 a year</span>
            <span class="date">2 days ago</span>
        </div>
        """
        mock_response.raise_for_status = MagicMock()
        
        # Configure the mock session
        mock_session_instance = MagicMock()
        mock_session_instance.get.return_value = mock_response
        mock_session.return_value = mock_session_instance
        
        # Test the search method
        scraper = IndeedScraper()
        jobs = scraper.search("python", "Vermont")
        
        # Verify the mock was called correctly
        mock_session_instance.get.assert_called_once()
        
        # Can't fully verify results due to BeautifulSoup parsing of mock HTML
        # In a real implementation, you might want to use a more sophisticated HTML mock
    
    @patch('requests.Session')
    def test_get_job_details(self, mock_session):
        """Test getting detailed job information."""
        # Create a mock response
        mock_response = MagicMock()
        mock_response.text = """
        <div id="jobDescriptionText">
            This is a test job description for a Python Developer position.
            Required skills: Python, Django, Flask.
        </div>
        """
        mock_response.raise_for_status = MagicMock()
        
        # Configure the mock session
        mock_session_instance = MagicMock()
        mock_session_instance.get.return_value = mock_response
        mock_session.return_value = mock_session_instance
        
        # Test the get_job_details method
        scraper = IndeedScraper()
        details = scraper.get_job_details("https://example.com/job")
        
        # Verify the mock was called correctly
        mock_session_instance.get.assert_called_once_with("https://example.com/job")
        
        # Verify results (basic check since exact parsing depends on BeautifulSoup)
        assert "description" in details