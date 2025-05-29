from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
import os
import shutil
from fpdf import FPDF

app = FastAPI()

# Enable CORS
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

@app.post("/analyze")
async def analyze():
    try:
        summary_lines = []
        files = os.listdir(UPLOAD_DIR)
        if not files:
            return JSONResponse(status_code=400, content={"error": "No files found for analysis."})

        for filename in files:
            if filename != "ReviewReport.pdf":
                summary_lines.append(f"Reviewed file: {filename}")

        summary_text = "\n".join(summary_lines)

        # Generate PDF
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