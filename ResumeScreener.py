import streamlit as st
import pdfplumber
import re
from transformers import pipeline
import pickle
import os

def extract_text_from_pdf(pdf_file):
    with pdfplumber.open(pdf_file) as pdf:
        text = ""
        for page in pdf.pages:
            text += page.extract_text()
    return text

def extract_gpa(text):
    gpa_pattern = r"GPA(?:\s*|:\s*)(\d+(?:\.\d+)?)"
    cgpa_pattern = r"CGPA(?:\s*|:\s*)(\d+(?:\.\d+)?)"
    
    gpa_match = re.search(gpa_pattern, text, re.IGNORECASE)
    cgpa_match = re.search(cgpa_pattern, text, re.IGNORECASE)
    
    if gpa_match:
        gpa = float(gpa_match.group(1))
    else:
        gpa = None
    
    if cgpa_match:
        cgpa = float(cgpa_match.group(1))
    else:
        cgpa = None
    
    return gpa, cgpa

def extract_technical_skills(text, job_category):
    skill_lists = {
        "Python Developer": ["Python", "SQL", "Flask", "Django"],
        "Frontend Developer": ["HTML", "CSS", "JavaScript", "React", "Angular", "Vue"],
        "Backend Developer": ["Python", "Java", "Node.js", "Express", "Spring Boot"],
        "Fullstack Developer": ["HTML", "CSS", "JavaScript", "Python", "React", "Angular", "Vue", "Node.js", "Express", "Django", "Flask"],
        "Data Scientist": ["Python", "R", "SQL", "Machine Learning", "Deep Learning", "Data Analysis"]
    }

    skill_list = skill_lists.get(job_category, ["Python"])

    extracted_skills = [skill for skill in skill_list if skill.lower() in text.lower()]
    return extracted_skills

def extract_years_of_experience(text):
    experience_pattern = r"(\d+)\s*(?:\+|-)?\s*years?\s*of\s*experience"
    experience_match = re.search(experience_pattern, text, re.IGNORECASE)
    
    if experience_match:
        years_of_experience = int(experience_match.group(1))
    else:
        years_of_experience = None
    
    return years_of_experience

def extract_projects(text):
    project_pattern = r"(?i)project\s*[\d+]:?\s*(.*?)\s*(?=(?:project|$))"
    projects = re.findall(project_pattern, text)
    return projects

# Function to calculate score for each resume
def calculate_score(gpa, technical_skills, years_of_experience, gpa_weight, skills_weight, exp_weight):
    score = (gpa * gpa_weight if gpa else 0) + \
            (len(technical_skills) * skills_weight) + \
            (years_of_experience * exp_weight if years_of_experience else 0)
    
    normalized_score = min(max(score / 10, 0), 10)
    
    rounded_score = round(normalized_score, 2)
    
    return rounded_score

# Define the Streamlit app layout
def main():
    st.title("Resume Evaluation and Ranking")

    job_category = st.selectbox("Select Job Category", ["Python Developer", "Frontend Developer", "Backend Developer", "Fullstack Developer", "Data Scientist"], index=0)

    uploaded_files = st.file_uploader("Upload PDF Resumes", accept_multiple_files=True, type="pdf")

    st.sidebar.title("Set Weightage for Criteria")
    gpa_weight = st.sidebar.slider("GPA/CGPA Weight", min_value=0, max_value=10, value=2, step=1)
    skills_weight = st.sidebar.slider("Technical Skills Weight", min_value=0, max_value=10, value=3, step=1)
    exp_weight = st.sidebar.slider("Years of Experience Weight", min_value=0, max_value=10, value=5, step=1)

    pipeline_file = "summarization_pipeline.pkl"

    if os.path.exists(pipeline_file):
        with open(pipeline_file, "rb") as f:
            summarizer = pickle.load(f)
    else:
        summarizer = pipeline("summarization", max_length=300, min_length=50)  # Adjust max_length and min_length as needed
        with open(pipeline_file, "wb") as f:
            pickle.dump(summarizer, f)

    if uploaded_files:
        resume_data = []
        scores = []
        st.write("Uploaded Resumes:")
        for file in uploaded_files:
            resume_text = extract_text_from_pdf(file)
            
            gpa, cgpa = extract_gpa(resume_text)
            technical_skills = extract_technical_skills(resume_text, job_category)
            years_of_experience = extract_years_of_experience(resume_text)
            
            projects = extract_projects(resume_text)
            
            score = calculate_score(gpa, technical_skills, years_of_experience, gpa_weight, skills_weight, exp_weight)
            
            summary = summarizer(resume_text, max_length=300, min_length=100, do_sample=False)[0]["summary_text"]
            
            summary += f"CGPA: {cgpa}\n" if cgpa else "\n"
            summary += f"Years of Experience: {years_of_experience}\n" if years_of_experience else "\n"
            summary += f"Technical SKills: {technical_skills}\n" if technical_skills else "\n"
            
            resume_data.append({"file_name": file.name, "summary": summary, "score": score})
            scores.append(score)
        
        sorted_resumes = sorted(resume_data, key=lambda x: x["score"], reverse=True)
        
        # Search bar
        search_term = st.text_input("Search for Keywords")
        
        # Filter resumes based on search term
        filtered_resumes = [resume for resume in sorted_resumes if search_term.lower() in resume["summary"].lower()]
        
        if filtered_resumes:
            st.write("Search Results:")
            for resume in filtered_resumes:
                st.write(f"Resume: {resume['file_name']}")
                st.write("Summary:")
                st.write(resume['summary'])
                st.write(f"Score: {resume['score']}")
        else:
            st.write("No matching resumes found.")

if __name__ == "__main__":
    main()
