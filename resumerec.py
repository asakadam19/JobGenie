import streamlit as st
import requests
import spacy
import PyPDF2
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Load NLP Model
nlp = spacy.load("en_core_web_sm")

# DeepSeek API Key (Set your API key here)
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')

# Function to extract text from resume
def extract_text_from_file(uploaded_file):
    if uploaded_file is not None:
        file_extension = uploaded_file.name.split(".")[-1].lower()

        # Extract from PDF
        if file_extension == "pdf":
            pdf_reader = PyPDF2.PdfReader(uploaded_file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()

        # Extract from DOCX
        elif file_extension == "docx":
            doc = docx.Document(uploaded_file)
            text = "\n".join([para.text for para in doc.paragraphs])
            return text.strip()

        # Extract from TXT
        elif file_extension == "txt":
            return uploaded_file.read().decode("utf-8").strip()

        else:
            return "Unsupported file format. Please upload a PDF, DOCX, or TXT file."
    return ""

# Extract key skills from text
def extract_keywords(text):
    doc = nlp(text)
    keywords = [token.text.lower() for token in doc if token.is_alpha and not token.is_stop]
    return set(keywords)

# Get job-specific skills using DeepSeek API
def get_job_skills(job_title):
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    prompt = f"List the essential skills for a {job_title} role, categorized as: Hard Skills (technical) and Soft Skills (communication, teamwork)."
    
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }

    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return "Error fetching job skills from DeepSeek API."

# Analyze resume for job match
def analyze_resume(resume_text, job_skills):
    resume_keywords = extract_keywords(resume_text)
    job_keywords = extract_keywords(job_skills)

    matched_skills = resume_keywords.intersection(job_keywords)
    missing_skills = job_keywords - resume_keywords

    # Resume Strength Score (Percentage of job-related skills present)
    strength_score = round((len(matched_skills) / len(job_keywords)) * 100, 2) if job_keywords else 0

    return {
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "strength_score": strength_score
    }

# DeepSeek API - Generate Resume Improvement Suggestions
def get_resume_improvement_tips(resume_text, job_title, matched_skills, missing_skills):
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    prompt = f"""
    I am applying for a {job_title} position.

    Here is my resume content:
    
    {resume_text}

    My resume currently matches these skills: {', '.join(matched_skills)}.
    However, I am missing these skills: {', '.join(missing_skills)}.

    Provide brief and direct resume improvement suggestions:
    1. Two Ways to Improve Resume(Keep each point under 20 words).
    2. Rephrase Two Sections for Better Impact:
        - Current Version: Show one weak bullet point from my resume.
        - Improved Version: Rewrite with measurable impact (use actual figures where possible).
    """

    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }

    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return "Error fetching resume improvement suggestions from DeepSeek API."

