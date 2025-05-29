from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
import os
import shutil
from fpdf import FPDF

app = FastAPI()

# ✅ Enable CORS for all domains (adjust for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or ["https://nspxn.com"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ✅ Upload endpoint
@app.post("/upload")
async def upload_files(files: list[UploadFile] = File(...)):
    filenames = []
    for file in files:
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        filenames.append(file.filename)
    return {"filenames": filenames}

# ✅ Mock analyze endpoint that returns a PDF
@app.post("/analyze")
async def analyze():
    output_path = os.path.join(UPLOAD_DIR, "ReviewReport.pdf")
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="NSPXN Auto Estimate AI Review", ln=True)
    pdf.multi_cell(0, 10, txt="This is a sample AI-generated report.\n\nFiles received:\n")

    for filename in os.listdir(UPLOAD_DIR):
        if filename != "ReviewReport.pdf":
            pdf.cell(0, 10, txt=f"- {filename}", ln=True)

    pdf.output(output_path)
    return FileRespons


@app.post("/analyze")
async def analyze():
    result_text = analyze_files(UPLOAD_DIR)
    pdf_path = create_pdf(result_text, UPLOAD_DIR)
    return FileResponse(pdf_path, media_type='application/pdf', filename="ReviewReport.pdf")
