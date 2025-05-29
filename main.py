import os
import re
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

def extract_metadata(text):
    claim_match = re.search(r"(?:Claim|File|Reference)\s*#?:?\s*([A-Z0-9-]{6,})", text, re.IGNORECASE)
    vin_match = re.search(r"\b([A-HJ-NPR-Z\d]{17})\b", text)
    vehicle_match = re.search(r"\d{4}\s+[^\n]+?(?:SEDAN|COUPE|SUV|FWD|UTV|TRUCK|VAN|WAGON)[^\n]*", text, re.IGNORECASE)

    return {
        "claim_number": claim_match.group(1) if claim_match else "N/A",
        "vin": vin_match.group(1) if vin_match else "N/A",
        "vehicle_description": vehicle_match.group(0).strip() if vehicle_match else "N/A"
    }

def score_response(response_text):
    violations = len(re.findall(r"(non-compliant|missing|error|issue|violation)", response_text, re.IGNORECASE))
    if violations == 0:
        return "100%"
    score = max(0, 100 - (violations * 10))
    return f"{score}%"

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
    metadata = extract_metadata(text_combined)

    text_block = {
        "type": "text",
        "text": f"""You are an expert auto damage appraiser. Compare the uploaded vehicle damage images to the written estimate and client rules below.

Client Rules:
{client_rules}

Estimate Text:
{text_combined}
"""
    }

    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a compliance-focused auto damage reviewer. Return detailed findings."},
                {"role": "user", "content": images + [text_block]}
            ],
            max_tokens=2000,
            temperature=0.2
        )

        result_text = response.choices[0].message.content
        score = score_response(result_text)

        return {
            "file_number": file_number,
            "claim_number": metadata["claim_number"],
            "vin": metadata["vin"],
            "vehicle": metadata["vehicle_description"],
            "score": score,
            "result": result_text
        }
    except Exception as e:
        return { "error": str(e) }