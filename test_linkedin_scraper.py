import unittest
from unittest.mock import patch, MagicMock
import json
import http.client
from io import BytesIO
from linkedin_api_scraper import scrape_linkedin_jobs, display_jobs

class TestLinkedInScraper(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        # Sample job data for testing
        self.sample_job = {
            "job_title": "Senior Data Engineer",
            "company_name": "Tech Corp",
            "location": "San Francisco, CA",
            "job_type": "Full-time",
            "posted_time": "2 days ago",
            "job_description": "Looking for an experienced Data Engineer...",
            "job_url": "https://linkedin.com/jobs/1234",
            "salary": "$150,000 - $200,000",
            "company_logo": "https://example.com/logo.png",
            "company_url": "https://techcorp.com",
            "experience_level": "Senior",
            "employment_type": "Full-time",
            "industry": "Technology"
        }
        
        # Sample API response
        self.sample_response = {
            "data": [self.sample_job]
        }

    @patch('http.client.HTTPSConnection')
    @patch('os.getenv')
    def test_successful_api_call(self, mock_getenv, mock_https_conn):
        """Test successful API call and data processing"""
        # Mock environment variables
        mock_getenv.return_value = "fake-api-key"
        
        # Mock HTTP response
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = json.dumps(self.sample_response).encode('utf-8')
        
        # Mock connection
        mock_conn = MagicMock()
        mock_conn.getresponse.return_value = mock_response
        mock_https_conn.return_value = mock_conn
        
        # Call the function
        jobs = scrape_linkedin_jobs("data engineer", "San Francisco")
        
        # Verify the results
        self.assertEqual(len(jobs), 1)
        job = jobs[0]
        self.assertEqual(job['Title'], "Senior Data Engineer")
        self.assertEqual(job['Company'], "Tech Corp")
        self.assertEqual(job['Location'], "San Francisco, CA")
        
        # Verify API call parameters
        mock_https_conn.assert_called_with("linkedin-data-api.p.rapidapi.com")
        mock_conn.request.assert_called_once()

    @patch('http.client.HTTPSConnection')
    @patch('os.getenv')
    def test_api_error_response(self, mock_getenv, mock_https_conn):
        """Test handling of API error response"""
        # Mock environment variables
        mock_getenv.return_value = "fake-api-key"
        
        # Mock error response
        mock_response = MagicMock()
        mock_response.status = 404
        
        # Mock connection
        mock_conn = MagicMock()
        mock_conn.getresponse.return_value = mock_response
        mock_https_conn.return_value = mock_conn
        
        # Call the function
        jobs = scrape_linkedin_jobs("data engineer", "San Francisco")
        
        # Verify empty result on error
        self.assertEqual(len(jobs), 0)

    @patch('http.client.HTTPSConnection')
    @patch('os.getenv')
    def test_missing_api_key(self, mock_getenv, mock_https_conn):
        """Test handling of missing API key"""
        # Mock missing API key
        mock_getenv.return_value = None
        
        # Call the function
        jobs = scrape_linkedin_jobs("data engineer", "San Francisco")
        
        # Verify empty result
        self.assertEqual(len(jobs), 0)
        
        # Verify no API call was made
        mock_https_conn.assert_not_called()

    def test_display_jobs_empty(self):
        """Test display_jobs with empty job list"""
        with patch('builtins.print') as mock_print:
            display_jobs([])
            mock_print.assert_called_with("\nNo jobs found.")

    def test_display_jobs_with_data(self):
        """Test display_jobs with sample data"""
        jobs = [{
            'Title': "Test Job",
            'Company': "Test Corp",
            'Location': "Test City",
            'Job Type': "Full-time",
            'Posted': "1 day ago",
            'Description': "Test description",
            'URL': "https://test.com",
            'Salary': "$100k",
            'Experience Level': "Mid",
            'Employment Type': "Full-time",
            'Industry': "Tech"
        }]
        
        with patch('builtins.print') as mock_print:
            display_jobs(jobs)
            # Verify that print was called multiple times
            self.assertTrue(mock_print.call_count > 5)

    def test_special_characters_in_search(self):
        """Test handling of special characters in search parameters"""
        with patch('http.client.HTTPSConnection') as mock_https_conn:
            # Test with special characters
            scrape_linkedin_jobs("C++ Developer", "New York, NY")
            
            # Verify the connection was attempted
            mock_https_conn.assert_called_once()

    @patch('http.client.HTTPSConnection')
    def test_connection_error(self, mock_https_conn):
        """Test handling of connection error"""
        # Mock connection error
        mock_https_conn.side_effect = Exception("Connection failed")
        
        # Call the function
        jobs = scrape_linkedin_jobs("data engineer", "San Francisco")
        
        # Verify empty result on connection error
        self.assertEqual(len(jobs), 0)

def main():
    unittest.main()

if __name__ == '__main__':
    main()
