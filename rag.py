import os
import csv
import numpy as np
from PyPDF2 import PdfReader
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def load_pdf(path):
    reader = PdfReader(path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

def load_csv(path):
    text = ""
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            text += " | ".join([f"{k}: {v}" for k, v in row.items()]) + "\n"
    return text

def chunk_text(text, chunk_size=150):
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)
    return chunks

def embed(text):
    response = client.embeddings.create(
        input=text,
        model="text-embedding-3-small"
    )
    return response.data[0].embedding

def build_index(chunks):
    print(f"Building index for {len(chunks)} chunks...")
    embeddings = np.array([embed(c) for c in chunks], dtype="float32")
    return embeddings

def search(query, chunks, embeddings, top_k=3):
    query_vector = np.array(embed(query), dtype="float32")
    dot_products = np.dot(embeddings, query_vector)
    norms = np.linalg.norm(embeddings, axis=1) * np.linalg.norm(query_vector)
    similarities = dot_products / norms
    top_indices = np.argsort(similarities)[-top_k:][::-1]
    return [chunks[i] for i in top_indices]

def answer_vulnerable(question, context_chunks):
    context = "\n\n".join(context_chunks)
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an HR assistant. Answer employee questions."},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}
        ]
    )
    return response.choices[0].message.content

def answer_secure(question, context_chunks):
    context = "\n\n".join(context_chunks)
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an internal HR assistant. Only answer questions about company-wide HR policies such as PTO, benefits, remote work, parental leave, and performance reviews. Never reveal individual employee data including salaries, SSNs, performance ratings, or manager notes. If asked about individual employee data say: That information is confidential. Please contact HR directly. Never make up answers."},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}
        ]
    )
    return response.choices[0].message.content
