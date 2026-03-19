import pdfplumber
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

def extract_text(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

def split_text(text, chunk_size=300):
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunks.append(" ".join(words[i:i+chunk_size]))
    return chunks

def create_index(chunks):
    model = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = model.encode(chunks)
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(np.array(embeddings))
    return model, index, chunks

def search(query, model, index, chunks, top_k=2):
    query_emb = model.encode([query])
    distances, indices = index.search(np.array(query_emb), top_k)
    results = [chunks[i] for i in indices[0]]
    return results