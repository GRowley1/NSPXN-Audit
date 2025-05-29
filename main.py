import os
import openai
import base64
import docx
import pdfplumber
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import List

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

openai.api_key = os.getenv("OPENAI_API_KEY")

def extract_text_from_docx(file_bytes):
    try:
        document = docx.Document(file_bytes)
        return "\n".join([p.text for p in document.paragraphs])
    except:
        return "⚠️ Unable to extract text from DOCX"

def extract_text_from_pdf(file_bytes):
    try:
        with pdfplumber.open(file_bytes) as pdf:
            return "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
    except:
        return "⚠️ Unable to extract text from PDF"

@app.post("/vision-review")
async def vision_review(
    files: List[UploadFile] = File(...),
    client_rules: str = Form(...),
    file_number: str = Form(...)
):
    images = []
    texts = []

    for file in files:
        contents = await file.read()
        name = file.filename.lower()
        if name.endswith(('.jpg', '.jpeg', '.png')):
            b64_image = base64.b64encode(contents).decode("utf-8")
            images.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{b64_image}"
                }
            })
        elif name.endswith(".txt"):
            texts.append(contents.decode("utf-8", errors="ignore"))
        elif name.endswith(".docx"):
            from io import BytesIO
            texts.append(extract_text_from_docx(BytesIO(contents)))
        elif name.endswith(".pdf"):
            from io import BytesIO
            texts.append(extract_text_from_pdf(BytesIO(contents)))
        else:
            texts.append(f"⚠️ Skipped unsupported file: {file.filename}")

    text_combined = "\n\n".join(texts)

    text_block = {
        "type": "text",
        "text": f"""
You are an expert auto damage appraiser. Compare the uploaded vehicle damage images to the provided written estimate and verify:
1. Whether the described damage is visible in the photos.
2. If the estimate complies with these client rules:
{client_rules}

Estimate Text:
{text_combined}
"""
    }

    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are a compliance-focused auto damage reviewer."
                },
                {
                    "role": "user",
                    "content": images + [text_block]
                }
            ],
            max_tokens=2000,
            temperature=0.2
        )
        return { "file_number": file_number, "result": response.choices[0].message.content }
    except Exception as e:
        return { "error": str(e) }