import streamlit as st
import pdfplumber
import re
from transformers import pipeline
import pickle
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Function to extract text from PDF resumes
def extract_text_from_pdf(pdf_file):
    with pdfplumber.open(pdf_file) as pdf:
        text = ""
        for page in pdf.pages:
            text += page.extract_text()
    return text

# Function to extract GPA/CGPA from resume text
def extract_gpa(text):
    # Search for patterns indicating GPA/CGPA in the text using regular expressions
    gpa_pattern = r"GPA(?:\s*|:\s*)(\d+(?:\.\d+)?)"
    cgpa_pattern = r"CGPA(?:\s*|:\s*)(\d+(?:\.\d+)?)"
    
    # Find GPA/CGPA values in the text
    gpa_match = re.search(gpa_pattern, text, re.IGNORECASE)
    cgpa_match = re.search(cgpa_pattern, text, re.IGNORECASE)
    
    # Extract GPA/CGPA values if found
    if gpa_match:
        gpa = float(gpa_match.group(1))
    else:
        gpa = None
    
    if cgpa_match:
        cgpa = float(cgpa_match.group(1))
    else:
        cgpa = None
    
    # Return the extracted GPA/CGPA values
    return gpa, cgpa

# Function to extract technical skills from resume text
def extract_technical_skills(text, job_category):
    # Define skill lists based on job categories
    skill_lists = {
        "Python Developer": ["Python", "SQL", "Flask", "Django"],
        "Frontend Developer": ["HTML", "CSS", "JavaScript", "React", "Angular", "Vue"],
        "Backend Developer": ["Python", "Java", "Node.js", "Express", "Spring Boot"],
        "Fullstack Developer": ["HTML", "CSS", "JavaScript", "Python", "React", "Angular", "Vue", "Node.js", "Express", "Django", "Flask"],
        "Data Scientist": ["Python", "R", "SQL", "Machine Learning", "Deep Learning", "Data Analysis"]
    }

    # Get the skill list based on the selected job category
    skill_list = skill_lists.get(job_category, ["Python"])

    # Search for predefined list of technical skills in the text
    extracted_skills = [skill for skill in skill_list if skill.lower() in text.lower()]
    return extracted_skills

# Function to extract years of experience from resume text
def extract_years_of_experience(text):
    # Search for phrases indicating years of experience in the text using regular expressions
    experience_pattern = r"(\d+)\s*(?:\+|-)?\s*years?\s*of\s*experience"
    
    # Find years of experience values in the text
    experience_match = re.search(experience_pattern, text, re.IGNORECASE)
    
    # Extract years of experience if found
    if experience_match:
        years_of_experience = int(experience_match.group(1))
    else:
        years_of_experience = None
    
    # Return the extracted years of experience
    return years_of_experience

# Function to calculate score for each resume
def calculate_score(gpa, technical_skills, years_of_experience):
    # Define scoring criteria and weights
    gpa_weight = 2
    technical_skills_weight = 3
    years_of_experience_weight = 5

    # Calculate score based on criteria and weights
    score = (gpa * gpa_weight if gpa else 0) + \
            (len(technical_skills) * technical_skills_weight) + \
            (years_of_experience * years_of_experience_weight if years_of_experience else 0)
    
    # Normalize score to range from 0 to 10
    normalized_score = min(max(score / 10, 0), 10)
    
    # Round the score to two decimal places
    rounded_score = round(normalized_score, 2)
    
    return rounded_score

# Function to send confirmation email
def send_confirmation_email(email):
    # Email server configuration
    smtp_server = "your-smtp-server"
    smtp_port = 587
    smtp_username = "your-smtp-username"
    smtp_password = "your-smtp-password"

    # Sender and recipient email addresses
    sender_email = "your-email@example.com"
    recipient_email = email

    # Create message object
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = recipient_email
    message["Subject"] = "Job Confirmation"

    # Email body
    body = "Dear Candidate,\n\nCongratulations! You have been selected for the job. Please reply to this email to confirm your acceptance.\n\nBest regards,\nYour Company"
    message.attach(MIMEText(body, "plain"))

    # Connect to SMTP server and send email
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.send_message(message)

# Define the Streamlit app layout
def main():
    st.title("Resume Evaluation and Ranking")

    # Dropdown menu to select job category
    job_category = st.selectbox("Select Job Category", ["Python Developer", "Frontend Developer", "Backend Developer", "Fullstack Developer", "Data Scientist"], index=0)

    # Upload resumes
    uploaded_files = st.file_uploader("Upload PDF Resumes", accept_multiple_files=True, type="pdf")

    # Load or initialize the summarizer object
    pipeline_file = "summarization_pipeline.pkl"

    if os.path.exists(pipeline_file):
        with open(pipeline_file, "rb") as f:
            summarizer = pickle.load(f)
    else:
        summarizer = pipeline("summarization")
        with open(pipeline_file, "wb") as f:
            pickle.dump(summarizer, f)

    # Display uploaded resumes, summaries, and scores
    if uploaded_files:
        resume_data = []
        st.write("Uploaded Resumes:")
        for file in uploaded_files:
            # Extract text from PDF resume
            resume_text = extract_text_from_pdf(file)
            
            # Extract GPA/CGPA, technical skills, and years of experience
            gpa, cgpa = extract_gpa(resume_text)
            technical_skills = extract_technical_skills(resume_text, job_category)
            years_of_experience = extract_years_of_experience(resume_text)
            
            # Calculate score
            score = calculate_score(gpa, technical_skills, years_of_experience)
            
           
