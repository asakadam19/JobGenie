from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
from time import sleep
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from random import randint
import math 
import logging
logging.disable(logging.CRITICAL)
import json
import math
import http.client
import json
import logging
from selenium.webdriver.common.keys import Keys
import pandas as pd
import PyPDF2
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.corpus import stopwords
import re
import os
from dotenv import load_dotenv

# Load the environment variables
load_dotenv()

def get_webdriver():
    try:
        print("Debug - Initializing Chrome WebDriver...")
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        
        # Set up custom user agent for Mac
        options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                           "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Initialize ChromeDriverManager with specific version and OS
        manager = ChromeDriverManager()
        driver_path = manager.install()
        # print(f"Debug - ChromeDriver path: {driver_path}")
        
        # Initialize the service
        service = Service(executable_path=driver_path)
        
        # Create and return the driver
        driver = webdriver.Chrome(service=service, options=options)
        # print("Debug - Chrome WebDriver initialized successfully")
        return driver
        
    except Exception as e:
        print(f"Debug - Error initializing Chrome WebDriver: {str(e)}")
        raise

# Not being used
def scrape_indeed_jobs(job_title, location, page = 1):
    jobs_per_page = 10  # Number of jobs per page
    base_url = "https://www.indeed.com/jobs"
    url_template = f"?q={job_title.replace(' ', '+')}&l={location.replace(' ', '+')}&sort=date"

    job_list = []  # List to store all job details
    seen_jobs = set()  # To track unique jobs based on (Title, Company, Location)
    num_jobs = page * 15
    
    for i in range(page):
        start = i * jobs_per_page
        url = base_url + url_template + f"&start={start}"
        driver = get_webdriver()
        driver.get(url)
        time.sleep(2)

        while True:
            try:
                # Wait for the job listings to load
                WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CLASS_NAME, "job_seen_beacon")))
            except Exception as e:
                break

            # Parse the current page
            html_content = driver.page_source
            soup = BeautifulSoup(html_content, "html.parser")

            # Extract job postings
            jobs = soup.find_all("div", class_="job_seen_beacon")

            if not jobs:
                break  # Stop if no jobs are found

            for job in jobs:
                try:
                    title_element = job.find("span", id=lambda x: x and x.startswith("jobTitle"))
                    title = title_element.text.strip() if title_element else "N/A"

                    company_element = job.find("span", attrs={"data-testid": "company-name"})
                    company = company_element.text.strip() if company_element else "N/A"

                    location_element = job.find("div", attrs={"data-testid": "text-location"})
                    job_location = location_element.text.strip() if location_element else "N/A"
                    
                    # Create a unique identifier for the job
                    job_id = (title, company, job_location)
                    
                    if job_id in seen_jobs:
                        continue  # Skip this job if it's a duplicate

                    # Add to the set of seen jobs
                    seen_jobs.add(job_id)

                    # Extract job link
                    link_element = job.find("a", href=True)
                    job_link = "https://www.indeed.com" + link_element["href"] if link_element else "N/A"

                    # Visit the job link to fetch the description
                    description = "N/A"
                    if job_link != "N/A":
                        driver = get_webdriver()
                        driver.get(job_link)
                        time.sleep(2)  # Allow the job description to load
                        job_page_html = driver.page_source
                        job_soup = BeautifulSoup(job_page_html, "html.parser")
                        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "jobDescriptionText")))
                        description_element = driver.find_element(By.ID, "jobDescriptionText")
                        description = description_element.text.strip() if description_element else "N/A"

                    # Append job details to the list
                    job_list.append({
                        "Title": title,
                        "Company": company,
                        "Location": job_location,
                        "Link": job_link,
                        "Description": description,
                    })

                except Exception as e:
                    print(f"Error extracting job: {e}")
                    
                # Stop if we've collected the required number of jobs
                if len(job_list) >= num_jobs:
                    break


    driver.quit()
    return job_list



def scrape_linkedin_jobs(search_term, location, page = 1):
    print("\n=== Starting LinkedIn Job Search ===")
    # Access variables
    RAPID_API_KEY = os.getenv("RAPID_API_KEY")
    JOB_SEARCH_URL = os.getenv("JOB_SEARCH_URL")
    JOB_SEARCH_X_RAPIDAPI_HOST = os.getenv("JOB_SEARCH_X_RAPIDAPI_HOST")
    
    # Initialize jobs list
    jobs_list = []
    
    try:
        # Establish connection to RapidAPI
        #print("Debug - Connecting to LinkedIn API...")
        conn = http.client.HTTPSConnection(JOB_SEARCH_X_RAPIDAPI_HOST)

        # API request payload
        payload = json.dumps({
            "search_terms": search_term,
            "location": location,
            "page": page
        })

        # Request headers
        headers = {
            "x-rapidapi-key": RAPID_API_KEY,
            "x-rapidapi-host": JOB_SEARCH_X_RAPIDAPI_HOST,
            "Content-Type": "application/json"
        }

        # Send POST request
        # print("Debug - Sending request to LinkedIn API...")
        conn.request("POST", "/", payload, headers)
        res = conn.getresponse()
        # print(f"Debug - API Response Status: {res.status}")
        
        if res.status != 200:
            # print(f"Debug - API Error: Status {res.status}")
            return []
            
        data = res.read()
        decoded_data = data.decode("utf-8")
        json_response = json.loads(decoded_data)
        
        if not isinstance(json_response, list):
            print(f"Debug - Unexpected API response format: {type(json_response)}")
            return []
            
        # print(f"Debug - Found {len(json_response)} jobs from API")
        
        # Process each job from the API response
        for job in json_response:
            try:
                # Extract basic job details
                job_details = {
                    "Title": job.get("job_title", "N/A"),
                    "Company": job.get("company_name", "N/A"),
                    "Location": job.get("job_location", "N/A"),
                    "Link": job.get("linkedin_job_url_cleaned", "N/A"),
                    "Description": job.get("job_description", "")
                }
                
                # If we don't have a description from the API, try to get it from the job URL
                if not job_details["Description"] and job_details["Link"] != "N/A":
                    driver = None
                    try:
                        #print(f"Debug - Fetching description from: {job_details['Link']}")
                        driver = get_webdriver()
                        
                        # Set page load timeout
                        driver.set_page_load_timeout(20)
                        
                        # Try to load the page
                        try:
                            driver.get(job_details["Link"])
                        except Exception as e:
                            print(f"Debug - Page load timeout: {e}")
                            driver.quit()
                            driver = None
                            raise
                        
                        # Wait for any one of the description containers to be present
                        description_selectors = [
                            "//div[contains(@class, 'show-more-less-html__markup')]",
                            "//div[contains(@class, 'jobs-description__content')]",
                            "//div[contains(@class, 'description__text')]",
                            "//div[contains(@class, 'jobs-box__html-content')]"
                        ]
                        
                        # Wait for any of the selectors to be present
                        for xpath in description_selectors:
                            try:
                                element = WebDriverWait(driver, 10).until(
                                    EC.presence_of_element_located((By.XPATH, xpath))
                                )
                                if element:
                                    # Scroll element into view
                                    driver.execute_script("arguments[0].scrollIntoView(true);", element)
                                    time.sleep(1)
                                    
                                    # Try different methods to get text
                                    text = element.text.strip()
                                    if not text:
                                        text = driver.execute_script("return arguments[0].textContent;", element).strip()
                                    
                                    if text and len(text) > 50:
                                        # print(f"Debug - Found description using {xpath} ({len(text)} chars)")
                                        job_details["Description"] = text
                                        break
                            except Exception as e:
                                # print(f"Debug - Selector {xpath} failed: {e}")
                                continue
                        
                        if job_details["Description"] == "":
                           # print("Debug - No description found with any selector")
                            job_details["Description"] = "No description available"
                            
                    except Exception as e:
                       # print(f"Debug - Error fetching description: {e}")
                        job_details["Description"] = "No description available"
                    finally:
                        if driver:
                            try:
                                driver.quit()
                            except Exception as e:
                                print(f"Debug - Error closing driver: {e}")
                
                jobs_list.append(job_details)
                #print(f"Debug - Processed job: {job_details['Title']} at {job_details['Company']}")
                
            except Exception as e:
                print(f"Debug - Error processing job: {e}")
                continue
    
    except Exception as e:
        print(f"Debug - LinkedIn API Error: {e}")
    
    print(f"Debug - Total jobs collected: {len(jobs_list)}")
    return jobs_list