from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
import os
import shutil
from fpdf import FPDF
import fitz  # PyMuPDF
import docx
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
STATIC_DIR = "static"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

@app.get("/")
def root():
    return {"message": "NSPXN AI Audit API is live"}

@app.post("/upload")
async def upload_files(files: list[UploadFile] = File(...)):
    filenames = []
    for file in files:
        path = os.path.join(UPLOAD_DIR, file.filename)
        with open(path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        filenames.append(file.filename)
    return {"filenames": filenames}

def extract_text_from_file(filepath):
    try:
        if filepath.endswith(".pdf"):
            doc = fitz.open(filepath)
            return "\n".join(page.get_text() for page in doc)
        elif filepath.endswith(".docx"):
            d = docx.Document(filepath)
            return "\n".join(p.text for p in d.paragraphs)
        elif filepath.endswith(".txt"):
            with open(filepath, "r", encoding="utf-8") as f:
                return f.read()
        else:
            return ""
    except Exception as e:
        return f"[Error reading {filepath}: {e}]"

def generate_ai_comparison(texts):
    prompt = (
        "Compare and summarize the differences, similarities, and issues found in these auto estimate documents. "
        "Mention mismatched parts, missing procedures, or consistency gaps.\n\n"
        + "\n\n---\n\n".join(texts)
    )
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1000
    )
    return response.choices[0].message["content"]

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    # Your OpenAI API call
except Exception as e:
    logger.error(f"An error occurred: {e}")
@app.post("/analyze")
async def analyze():
    try:
        files = os.listdir(UPLOAD_DIR)
        if not files:
            return JSONResponse(status_code=400, content={"error": "No files to analyze."})

        texts = []
        for filename in files[:3]:  # Limit to 3 files
            path = os.path.join(UPLOAD_DIR, filename)
            text = extract_text_from_file(path)
            if text:
                texts.append(f"{filename}:\n{text[:2000]}")  # Limit per file

        if not texts:
            return JSONResponse(status_code=400, content={"error": "No readable content found."})

        summary_text = generate_ai_comparison(texts)

        # Write PDF
        pdf_path = os.path.join(STATIC_DIR, "ReviewReport.pdf")
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, "NSPXN AI Audit Summary\n\n" + summary_text)
        pdf.output(pdf_path)

        return {
            "summary": summary_text,
            "pdf_url": "/static/ReviewReport.pdf"
        }

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
