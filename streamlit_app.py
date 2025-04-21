import streamlit as st
import requests
import pandas as pd
from PyPDF2 import PdfReader
from io import BytesIO  # For creating in-memory Excel files
from nltk_setup import setup_nltk
import resumerec

# Initialize NLTK once at startup
setup_nltk()

# Streamlit Page Configuration
st.set_page_config(page_title="JobGenie", layout="wide")

# Title
st.title("JobGenie")

tab1, tab2 = st.tabs(["🔍 Find Jobs", "📄 Resume Analysis"])
with tab1:
    st.subheader("Upload your resume and find the best jobs for you!")

    # Resume Upload Function
    def extract_text_from_pdf(file):
        reader = PdfReader(file)
        text = " ".join(page.extract_text() for page in reader.pages)
        return text

    # Resume Upload
    uploaded_file = st.file_uploader("Upload your resume (PDF or Word)", type=["pdf", "docx"])
    if uploaded_file:
        if uploaded_file.type == "application/pdf":
            resume_text = extract_text_from_pdf(uploaded_file)
        else:
            resume_text = uploaded_file.read().decode("utf-8", errors="ignore")
        st.success("Resume uploaded successfully!")
    else:
        resume_text = None

    # Job Search Inputs
    job_title = st.text_input("Enter job title:")
    job_location = st.text_input("Enter job location:")

    # Additional Filters
    #days_old = st.number_input("Filter jobs posted in the last X days:", min_value=1, max_value=30, value=7)
    num_pages = st.number_input("Number of pages to fetch:", min_value=1, max_value=10, value=1)

    # Include Source Options
    # st.write("Include Results From:")
    # include_indeed = st.checkbox("Indeed", value=True)
    # include_linkedin = st.checkbox("LinkedIn", value=True)

    if st.button("Find Jobs"):
        if not resume_text or not job_title:
            st.error("Please upload a resume and provide a job title!")
        else:
            # Show loading message
            with st.spinner('Searching for jobs... This may take a few minutes...'):
                st.info(f"Searching for {job_title} jobs in {job_location if job_location else 'any location'}")
                # Call the backend API
                try:
                    response = requests.post("http://127.0.0.1:5004/recommend_jobs", json={
                        "resume": resume_text,
                        "job_title": job_title,
                        "location": job_location,
                        "days_old": 7,
                        "num_pages": num_pages,
                        "include_indeed": 0,
                        "include_linkedin": 1
                    })

                    if response.status_code == 200:
                        jobs = response.json()
                        if jobs:
                            # Convert JSON response to DataFrame
                            jobs_df = pd.DataFrame(jobs)

                            # Select and display relevant columns
                            if not jobs_df.empty:
                                st.write("Recommended Jobs:")
                                st.dataframe(
                                    jobs_df[["Title", "Company", "Location", "Similarity Score", "Link", "Description"]],
                                    column_config={
                                        "Link": st.column_config.LinkColumn(
                                            "Link",
                                            display_text="Link ⤴",  # This will display the actual URL with an arrow
                                            validate="^https?://.*"  # Validates that the link starts with http:// or https://
                                        ),
                                        "Similarity Score": st.column_config.NumberColumn(
                                            "Similarity Score",
                                            format="%.2f"
                                        )
                                    }
                                )

                                # Save the DataFrame as CSV
                                csv_data = jobs_df.to_csv(index=False)

                                # Save the DataFrame as Excel using BytesIO
                                excel_buffer = BytesIO()
                                jobs_df.to_excel(excel_buffer, index=False, engine='openpyxl')
                                excel_data = excel_buffer.getvalue()

                                # Download Buttons
                                st.download_button(
                                    label="Download as CSV",
                                    data=csv_data,
                                    file_name="recommended_jobs.csv",
                                    mime="text/csv",
                                )
                                st.download_button(
                                    label="Download as Excel",
                                    data=excel_data,
                                    file_name="recommended_jobs.xlsx",
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                )
                            else:
                                st.write("No jobs found matching your criteria.")
                        else:
                            st.write("No jobs found matching your criteria.")
                    else:
                        st.error(f"Failed to fetch jobs: {response.status_code}")

                except requests.exceptions.ConnectionError:
                    st.error("Could not connect to the job search service. Please ensure the backend server is running.")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
                    st.error("Please try again or contact support if the problem persists.")

with tab2:
    st.subheader("Upload your resume and get AI-Powered Resume Insights!")
    # Upload Resume
    uploaded_file = st.file_uploader("Upload Resume (PDF, DOCX, TXT)", type=["pdf", "docx", "txt"])

    # Input Job Title
    job_title = st.text_input("Enter the Job Title (e.g., Data Scientist, Software Engineer)")

    # Analyze Resume Button
    if uploaded_file and job_title:
        with st.spinner("Fetching job-specific skills..."):
            job_skills = resumerec.get_job_skills(job_title)

        with st.spinner("Analyzing Resume..."):
            resume_text = resumerec.extract_text_from_file(uploaded_file)
            if resume_text:
                result = resumerec.analyze_resume(resume_text, job_skills)

                # Chatbot Response
                st.subheader("🔍 Resume Analysis Report")
                st.write(f"*Impact Strength Score:* {result['strength_score']}%")

                # DeepSeek-Powered Resume Improvement Suggestions
                with st.spinner("Generating AI Resume Tips..."):
                    resume_tips = resumerec.get_resume_improvement_tips(resume_text, job_title, result['matched_skills'], result['missing_skills'])
                    st.subheader("🤖 AI-Powered Resume Improvement Suggestions")
                    st.write(resume_tips)

    else:
        st.info("📤 Please upload a resume and enter a job title to proceed.")