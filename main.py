import os
import openai
import base64
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from io import BytesIO

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

openai.api_key = os.getenv("OPENAI_API_KEY")

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
        ext = file.filename.lower()
        if ext.endswith(('.jpg', '.jpeg', '.png')):
            b64_image = base64.b64encode(contents).decode("utf-8")
            images.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{b64_image}"
                }
            })
        else:
            try:
                texts.append(contents.decode("utf-8", errors="ignore"))
            except:
                texts.append("Could not decode file: " + file.filename)

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