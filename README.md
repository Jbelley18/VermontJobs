# Vermont Jobs Tracker

A FastAPI application that scrapes job listings from various sources focused on Vermont job market, stores them in a database, and provides API endpoints to query the data.

## Features

- Scrapes jobs from Indeed, LinkedIn, and Vermont Job boards
- RESTful API with filtering capabilities (by keyword, location, salary, etc.)
- Background tasks for scheduled scraping
- Automatic API documentation with Swagger UI
- Database integration with SQLAlchemy

## Project Structure

```
vermont-jobs-tracker/
├── app/
│   ├── main.py           # FastAPI application
│   ├── database.py       # Database connection
│   ├── models.py         # Pydantic models
│   ├── schemas.py        # Database schemas
│   └── scraper/
│       ├── indeed.py     # Indeed scraper
│       ├── linkedin.py   # LinkedIn scraper
│       └── vtjobs.py     # Vermont jobs scraper
├── tests/
└── requirements.txt      # Dependencies
```

## Getting Started

1. **Setup a virtual environment**:
   ```bash
   # On Unix/MacOS
   python -m venv venv
   source venv/bin/activate
   
   # On Windows PowerShell
   python -m venv venv
   .\venv\Scripts\Activate  # Or .\venv\bin\Activate.ps1 on some setups
   ```

2. **Install dependencies**:
   ```bash
   # Standard installation
   pip install -r requirements.txt
   
   # If on Windows and encountering wheel building errors
   # Use the following command instead:
   pip install --prefer-binary -r requirements.txt
   
   # If still encountering issues with pydantic-core on Windows:
   # Edit requirements.txt and change "pydantic>=2.3.0" to "pydantic==1.10.8"
   ```

3. **Run the application**:
   ```bash
   cd vermont-jobs-tracker
   uvicorn app.main:app --reload
   ```

4. **Access the API documentation**:
   - Open your browser and navigate to http://127.0.0.1:8000/docs

## API Endpoints

- `GET /jobs`: Get all jobs with filtering options
- `GET /jobs/{job_id}`: Get a specific job by ID
- `GET /tags`: Get all available job tags
- `GET /stats`: Get job statistics
- `POST /jobs/scrape`: Trigger a job scraping run (admin endpoint)

## Development

### Adding a new job source

1. Create a new scraper module in the `app/scraper` directory
2. Implement the scraper similar to the existing ones
3. Import the scraper in `main.py` and add it to the `run_scrapers` function

## Running Tests

The project includes a comprehensive test suite covering the API endpoints, scraper functionality, and background tasks.

To run the tests:

```bash
# Run all tests
pytest

# Run tests with verbose output
pytest -v

# Run a specific test file
pytest tests/test_api.py

# Run tests with coverage report
pytest --cov=app
```

For the coverage report, you may need to install `pytest-cov`:

```bash
pip install pytest-cov
```

## Future Enhancements

- User authentication and accounts
- Saved job searches and email notifications
- Frontend UI for browsing jobs
- More granular job filters and advanced search
- Additional job sources