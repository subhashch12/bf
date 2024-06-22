import re
from pdfminer.high_level import extract_text
import spacy
from spacy.matcher import Matcher
from flask import Flask, request, jsonify, render_template
import os

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

nlp = spacy.load('en_core_web_sm')

def extract_text_from_pdf(pdf_path):
    return extract_text(pdf_path)

def extract_contact_number_from_resume(text):
    pattern = r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"
    match = re.search(pattern, text)
    return match.group() if match else None

def extract_email_from_resume(text):
    pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
    match = re.search(pattern, text)
    return match.group() if match else None

def extract_skills_from_resume(text, skills_list):
    skills = [skill for skill in skills_list if re.search(r"\b{}\b".format(re.escape(skill)), text, re.IGNORECASE)]
    return skills

def extract_education_from_resume(text):
    pattern = r"(?i)(?:Bsc|\bB\.\w+|\bM\.\w+|\bPh\.D\.\w+|\bBachelor(?:'s)?|\bMaster(?:'s)?|\bPh\.D)\s(?:\w+\s)*\w+"
    matches = re.findall(pattern, text)
    return [match.strip() for match in matches]

def extract_experience(text):
    pattern = r'(\d+)\s+years?\s+of\s+experience'
    match = re.search(pattern, text, re.IGNORECASE)
    return int(match.group(1)) if match else 0

def extract_name(resume_text):
    matcher = Matcher(nlp.vocab)
    patterns = [
        [{'POS': 'PROPN'}, {'POS': 'PROPN'}],
        [{'POS': 'PROPN'}, {'POS': 'PROPN'}, {'POS': 'PROPN'}],
        [{'POS': 'PROPN'}, {'POS': 'PROPN'}, {'POS': 'PROPN'}, {'POS': 'PROPN'}]
    ]
    for pattern in patterns:
        matcher.add('NAME', patterns=[pattern])
    doc = nlp(resume_text)
    matches = matcher(doc)
    for match_id, start, end in matches:
        span = doc[start:end]
        return span.text
    return None

def calculate_resume_score(skills, education, experience, skills_list):
    skill_score = len(skills) / len(skills_list) * 80
    education_score = 10 if any('Bsc' in edu or 'Bachelor' in edu for edu in education) else 0
    experience_score = 5 if experience >= 5 else experience / 5 * 5
    total_score = skill_score + education_score + experience_score
    return total_score, skill_score, education_score, experience_score

@app.route('/')
def upload_form():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return "No file part"
    file = request.files['file']
    if file.filename == '':
        return "No selected file"
    if file:
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)
        text = extract_text_from_pdf(file_path)
        
        name = extract_name(text)
        contact_number = extract_contact_number_from_resume(text)
        email = extract_email_from_resume(text)
        
        skills_list = ['Python', 'Data Analysis', 'Machine Learning', 'Communication', 'Project Management', 'Deep Learning', 'SQL', 'Tableau']
        extracted_skills = extract_skills_from_resume(text, skills_list)
        extracted_education = extract_education_from_resume(text)
        experience = extract_experience(text)
        
        total_score, skill_score, education_score, experience_score = calculate_resume_score(extracted_skills, extracted_education, experience, skills_list)
        
        result = {
            "Name": name,
            "Contact Number": contact_number,
            "Email": email,
            "Skills": extracted_skills,
            "Education": extracted_education,
            "Experience": experience,
            "Resume Score": total_score,
            "Skill Score": skill_score,
            "Education Score": education_score,
            "Experience Score": experience_score
        }
        
        return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
