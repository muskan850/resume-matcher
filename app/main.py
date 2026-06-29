from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from PyPDF2 import PdfReader
from docx import Document
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import io
import re

app = FastAPI()

SKILLS = [
    "python", "java", "javascript", "html", "css", "react", "node",
    "fastapi", "flask", "django", "sql", "mysql", "mongodb",
    "machine learning", "deep learning", "nlp", "pandas", "numpy",
    "scikit-learn", "excel", "power bi", "tableau", "git", "github",
    "communication", "leadership", "problem solving", "data analysis"
]

def clean_text(text):
    text = text.lower()
    text = re.sub(r"[^a-zA-Z0-9+#.\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def extract_pdf_text(file_bytes):
    reader = PdfReader(io.BytesIO(file_bytes))
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

def extract_docx_text(file_bytes):
    document = Document(io.BytesIO(file_bytes))
    return "\n".join([para.text for para in document.paragraphs])

def get_skills(text):
    text = clean_text(text)
    found = []
    for skill in SKILLS:
        if skill in text:
            found.append(skill)
    return sorted(set(found))

@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Resume Matcher</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background: #f5f7fb;
                padding: 40px;
            }
            .container {
                max-width: 800px;
                margin: auto;
                background: white;
                padding: 30px;
                border-radius: 12px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            }
            h1 {
                text-align: center;
                color: #333;
            }
            label {
                font-weight: bold;
                display: block;
                margin-top: 20px;
            }
            textarea {
                width: 100%;
                height: 180px;
                padding: 10px;
                margin-top: 8px;
            }
            input {
                margin-top: 8px;
            }
            button {
                margin-top: 25px;
                width: 100%;
                padding: 14px;
                background: #6c2bd9;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                cursor: pointer;
            }
            button:hover {
                background: #5521b5;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Resume Matcher</h1>
            <form action="/match" method="post" enctype="multipart/form-data">
                <label>Upload Resume PDF/DOCX</label>
                <input type="file" name="resume" accept=".pdf,.docx,.txt" required>

                <label>Paste Job Description</label>
                <textarea name="job_description" required></textarea>

                <button type="submit">Check Match</button>
            </form>
        </div>
    </body>
    </html>
    """

@app.post("/match", response_class=HTMLResponse)
async def match_resume(
    resume: UploadFile = File(...),
    job_description: str = Form(...)
):
    file_bytes = await resume.read()
    filename = resume.filename.lower()

    if filename.endswith(".pdf"):
        resume_text = extract_pdf_text(file_bytes)
    elif filename.endswith(".docx"):
        resume_text = extract_docx_text(file_bytes)
    elif filename.endswith(".txt"):
        resume_text = file_bytes.decode("utf-8", errors="ignore")
    else:
        return "<h2>Only PDF, DOCX, or TXT files are supported.</h2>"

    resume_text_clean = clean_text(resume_text)
    jd_clean = clean_text(job_description)

    vectorizer = TfidfVectorizer(stop_words="english")
    vectors = vectorizer.fit_transform([resume_text_clean, jd_clean])
    similarity = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]

    match_score = round(similarity * 100, 2)

    resume_skills = get_skills(resume_text)
    jd_skills = get_skills(job_description)

    matched_skills = sorted(set(resume_skills).intersection(set(jd_skills)))
    missing_skills = sorted(set(jd_skills).difference(set(resume_skills)))

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Resume Match Result</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background: #f5f7fb;
                padding: 40px;
            }}
            .container {{
                max-width: 800px;
                margin: auto;
                background: white;
                padding: 30px;
                border-radius: 12px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            }}
            h1 {{
                color: #333;
                text-align: center;
            }}
            .score {{
                font-size: 42px;
                text-align: center;
                color: #6c2bd9;
                font-weight: bold;
            }}
            .box {{
                background: #f1f1f1;
                padding: 15px;
                border-radius: 8px;
                margin-top: 15px;
            }}
            a {{
                display: block;
                margin-top: 25px;
                text-align: center;
                color: #6c2bd9;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Resume Match Result</h1>
            <div class="score">{match_score}%</div>

            <div class="box">
                <h3>Matched Skills</h3>
                <p>{", ".join(matched_skills) if matched_skills else "No matched skills found."}</p>
            </div>

            <div class="box">
                <h3>Missing Skills</h3>
                <p>{", ".join(missing_skills) if missing_skills else "No missing skills found."}</p>
            </div>

            <a href="/">Check another resume</a>
        </div>
    </body>
    </html>
    """
