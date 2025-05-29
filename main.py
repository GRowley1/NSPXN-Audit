from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
import os, shutil
from fpdf import FPDF

app = FastAPI()

# ✅ Proper CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Use your domain for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

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
        pdf_path = os.path.join(UPLOAD_DIR, "ReviewReport.pdf")
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 10, "NSPXN Auto Estimate Review", ln=True)
        pdf.ln(10)

        files = os.listdir(UPLOAD_DIR)
        if not files:
            return JSONResponse(status_code=400, content={"error": "No files to analyze."})

        for filename in files:
            if filename != "ReviewReport.pdf":
                pdf.cell(0, 10, f"- {filename}", ln=True)

        pdf.output(pdf_path)
        return FileResponse(pdf_path, media_type="application/pdf", filename="ReviewReport.pdf")
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

async def analyze():
    result_text = analyze_files(UPLOAD_DIR)
    pdf_path = create_pdf(result_text, UPLOAD_DIR)
    return FileResponse(pdf_path, media_type='application/pdf', filename="ReviewReport.pdf")
