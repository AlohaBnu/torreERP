import pdfplumber
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

# === 1. Ler PDF ===
def ler_pdf(caminho_pdf):
    texto = ""
    with pdfplumber.open(caminho_pdf) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                texto += page_text + " "
    return texto

# === 2. Dividir em chunks ===
def dividir_texto(texto, tamanho=500):
    return [texto[i:i+tamanho] for i in range(0, len(texto), tamanho)]

# === 3. Criar índice vetorial ===
def criar_indice(chunks):
    model = SentenceTransformer('all-MiniLM-L6-v2')
    embeddings = model.encode(chunks)
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(np.array(embeddings))
    return model, index, chunks

# === 4. Função para perguntas ===
def perguntar(query, model, index, chunks, k=3):
    query_emb = model.encode([query])
    D, I = index.search(np.array(query_emb), k)
    respostas = [chunks[idx] for idx in I[0]]
    return respostas

# === 5. Exemplo de uso ===
if __name__ == "__main__":
    texto = ler_pdf("documento.pdf")  # coloque o nome do seu PDF aqui
    chunks = dividir_texto(texto)
    model, index, chunks = criar_indice(chunks)

    # Pergunta de exemplo
    pergunta = "O que é CIV?"
    respostas = perguntar(pergunta, model, index, chunks)

    print("\n--- Resposta ---")
    for r in respostas:
        print(r)
        print("---------------")