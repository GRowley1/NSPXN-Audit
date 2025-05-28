import os
from openai import OpenAI

client = OpenAI()

def analyze_files(upload_dir):
    texts = []
    for filename in os.listdir(upload_dir):
        path = os.path.join(upload_dir, filename)
        if filename.endswith('.txt') or filename.endswith('.pdf'):
            with open(path, 'rb') as f:
                content = f.read()
            texts.append(f"File: {filename}\nContent: {content[:500]}...\n")
    prompt = "Compare the following auto damage estimate documents and provide a summary:\n" + "\n".join(texts)
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content