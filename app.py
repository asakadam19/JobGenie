from flask import Flask, request, jsonify
from job_search import scrape_indeed_jobs, scrape_linkedin_jobs
from similarity_score import calculate_similarity_tfidf
from dotenv import load_dotenv
from nltk_setup import setup_nltk
import os
import logging
import traceback
import sys

# Initialize NLTK once at startup
setup_nltk()

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

@app.route('/recommend_jobs', methods=['POST'])
def recommend_jobs():
    """
    Endpoint to recommend jobs based on user inputs.
    """
    try:
        # Get JSON data from the request
        data = request.json
        resume = data.get("resume")
        job_title = data.get("job_title")
        location = data.get("location", "")
        days_old = data.get("days_old", 7)
        num_pages = data.get("num_pages", 1)
        include_indeed = data.get("include_indeed", True)
        include_linkedin = data.get("include_linkedin", True)

        if not resume or not job_title:
            return jsonify({"error": "Resume and job title are required"}), 400

        all_jobs = []

        # Fetch jobs from Indeed
        if include_indeed:
            try:
                logging.info("Fetching jobs from Indeed...")
                logging.info(f"Parameters - Title: {job_title}, Location: {location}, Pages: {num_pages}")
                jobs_from_indeed = scrape_indeed_jobs(job_title, location, num_pages)
                if jobs_from_indeed:
                    logging.info(f"Found {len(jobs_from_indeed)} jobs from Indeed")
                    all_jobs.extend(jobs_from_indeed)
                else:
                    logging.warning("No jobs found from Indeed")
            except Exception as e:
                logging.error(f"Error fetching Indeed jobs: {str(e)}")
                logging.error(traceback.format_exc())

        # Fetch jobs from LinkedIn
        if include_linkedin:
            try:
                logging.info("Fetching jobs from LinkedIn...")
                logging.info(f"Parameters - Title: {job_title}, Location: {location}, Pages: {num_pages}")
                jobs_from_linkedin = scrape_linkedin_jobs(job_title, location, num_pages)
                if jobs_from_linkedin:
                    logging.info(f"Found {len(jobs_from_linkedin)} jobs from LinkedIn")
                    all_jobs.extend(jobs_from_linkedin)
                else:
                    logging.warning("No jobs found from LinkedIn")
            except Exception as e:
                logging.error(f"Error fetching LinkedIn jobs: {str(e)}")
                logging.error(traceback.format_exc())

        # Add similarity scores to each job
        for job in all_jobs:
            job_description = job.get("Description", "")
            tfidf_score = calculate_similarity_tfidf(resume, job_description) if job_description else 0.0
            job["Similarity Score"] = round(tfidf_score, 4)

        # Sort jobs by similarity score (highest to lowest)
        sorted_jobs = sorted(all_jobs, key=lambda x: x["Similarity Score"], reverse=True)

        return jsonify(sorted_jobs), 200

    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        logging.error(f"An error occurred: {str(e)}")
        logging.error("Exception type: %s", exc_type)
        logging.error("Exception traceback: %s", traceback.format_exc())
        return jsonify({"error": f"An internal error occurred: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5004)