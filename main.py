from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import shutil, os
from ai_logic import analyze_files
from pdf_generator import create_pdf

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"

@app.post("/upload")
async def upload_files(files: list[UploadFile] = File(...)):
    filepaths = []
    for file in files:
        path = os.path.join(UPLOAD_DIR, file.filename)
        with open(path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        filepaths.append(path)
    return {"filenames": filepaths}

@app.post("/analyze")
async def analyze():
    result_text = analyze_files(UPLOAD_DIR)
    pdf_path = create_pdf(result_text, UPLOAD_DIR)
    return FileResponse(pdf_path, media_type='application/pdf', filename="ReviewReport.pdf")