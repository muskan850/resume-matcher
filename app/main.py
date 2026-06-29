from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from PyPDF2 import PdfReader
from docx import Document
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List
import io
import re
import html

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

def calculate_match_score(resume_text, job_description):
    resume_text_clean = clean_text(resume_text)
    jd_clean = clean_text(job_description)

    if not resume_text_clean or not jd_clean:
        return 0.0

    vectorizer = TfidfVectorizer(stop_words="english")
    vectors = vectorizer.fit_transform([resume_text_clean, jd_clean])
    similarity = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]

    return round(similarity * 100, 2)

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
                max-width: 900px;
                margin: auto;
                background: white;
                padding: 30px;
                border-radius: 12px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            }
            h1 {
                text-align: center;
                color: #333;
                font-size: 40px;
            }
            label {
                font-weight: bold;
                display: block;
                margin-top: 20px;
                font-size: 20px;
            }
            textarea {
                width: 100%;
                height: 220px;
                padding: 10px;
                margin-top: 8px;
                font-size: 16px;
            }
            input {
                margin-top: 8px;
                font-size: 16px;
            }
            .hint {
                color: #555;
                font-size: 14px;
                margin-top: 6px;
            }
            button {
                margin-top: 25px;
                width: 100%;
                padding: 16px;
                background: #6c2bd9;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 18px;
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
                <label>Upload Multiple Resumes PDF/DOCX/TXT</label>
                <input type="file" name="resumes" accept=".pdf,.docx,.txt" multiple required>
                <div class="hint">Multiple files select karne ke liye Ctrl ya Shift press karke files select karo.</div>

                <label>Paste Job Description</label>
                <textarea name="job_description" required></textarea>

                <button type="submit">Check Match</button>
            </form>
        </div>
    </body>
    </html>
    """

@app.post("/match", response_class=HTMLResponse)
async def match_resumes(
    resumes: List[UploadFile] = File(...),
    job_description: str = Form(...)
):
    results = []

    jd_skills = get_skills(job_description)

    for resume in resumes:
        file_bytes = await resume.read()
        filename = resume.filename.lower()

        try:
            if filename.endswith(".pdf"):
                resume_text = extract_pdf_text(file_bytes)
            elif filename.endswith(".docx"):
                resume_text = extract_docx_text(file_bytes)
            elif filename.endswith(".txt"):
                resume_text = file_bytes.decode("utf-8", errors="ignore")
            else:
                results.append({
                    "filename": resume.filename,
                    "score": 0,
                    "matched_skills": [],
                    "missing_skills": [],
                    "status": "Unsupported file type"
                })
                continue

            match_score = calculate_match_score(resume_text, job_description)

            resume_skills = get_skills(resume_text)
            matched_skills = sorted(set(resume_skills).intersection(set(jd_skills)))
            missing_skills = sorted(set(jd_skills).difference(set(resume_skills)))

            results.append({
                "filename": resume.filename,
                "score": match_score,
                "matched_skills": matched_skills,
                "missing_skills": missing_skills,
                "status": "Success"
            })

        except Exception as e:
            results.append({
                "filename": resume.filename,
                "score": 0,
                "matched_skills": [],
                "missing_skills": [],
                "status": f"Error: {str(e)}"
            })

    results = sorted(results, key=lambda x: x["score"], reverse=True)

    rows = ""
    for index, result in enumerate(results, start=1):
        filename = html.escape(result["filename"])
        status = html.escape(result["status"])
        matched = html.escape(", ".join(result["matched_skills"]) if result["matched_skills"] else "No matched skills")
        missing = html.escape(", ".join(result["missing_skills"]) if result["missing_skills"] else "No missing skills")

        rows += f"""
        <tr>
            <td>{index}</td>
            <td>{filename}</td>
            <td><strong>{result["score"]}%</strong></td>
            <td>{matched}</td>
            <td>{missing}</td>
            <td>{status}</td>
        </tr>
        """

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Resume Match Results</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background: #f5f7fb;
                padding: 40px;
            }}
            .container {{
                max-width: 1200px;
                margin: auto;
                background: white;
                padding: 30px;
                border-radius: 12px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            }}
            h1 {{
                text-align: center;
                color: #333;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 25px;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 12px;
                text-align: left;
                vertical-align: top;
            }}
            th {{
                background: #6c2bd9;
                color: white;
            }}
            tr:nth-child(even) {{
                background: #f9f9f9;
            }}
            a {{
                display: block;
                margin-top: 25px;
                text-align: center;
                color: #6c2bd9;
                font-size: 18px;
                text-decoration: none;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Resume Match Results</h1>
            <table>
                <tr>
                    <th>Rank</th>
                    <th>Resume</th>
                    <th>Match Score</th>
                    <th>Matched Skills</th>
                    <th>Missing Skills</th>
                    <th>Status</th>
                </tr>
                {rows}
            </table>

            <a href="/">Check another set of resumes</a>
        </div>
    </body>
    </html>
    """
