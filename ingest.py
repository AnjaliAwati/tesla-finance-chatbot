import glob
import os
import re

import chromadb
from pypdf import PdfReader

from common import embed_texts, pick_embed_model

DATA_DIR = "data"
DB_DIR = "chroma_db"
CHUNK_SIZE = 1000
OVERLAP = 150


def chunk_text(text):
    chunks, start = [], 0
    while start < len(text):
        piece = text[start:start + CHUNK_SIZE].strip()
        if len(piece) > 100:
            chunks.append(piece)
        start += CHUNK_SIZE - OVERLAP
    return chunks


def main():
    pdfs = sorted(glob.glob(os.path.join(DATA_DIR, "*.pdf")))
    if not pdfs:
        print("No PDFs found in the data/ folder.")
        return

    docs, metas, ids = [], [], []
    for path in pdfs:
        name = os.path.basename(path)
        print(f"Reading {name} ...")
        reader = PdfReader(path)
        for page_no, page in enumerate(reader.pages, start=1):
            text = re.sub(r"\s+", " ", page.extract_text() or "")
            for i, chunk in enumerate(chunk_text(text)):
                docs.append(chunk)
                metas.append({"source": name, "page": page_no})
                ids.append(f"{name}-p{page_no}-{i}")
    print(f"Total chunks: {len(docs)}")

    embed_model = pick_embed_model()
    print(f"Embedding with: {embed_model} (this takes a few minutes)")
    vectors = embed_texts(docs, embed_model)

    client = chromadb.PersistentClient(path=DB_DIR)
    try:
        client.delete_collection("tesla")
    except Exception:
        pass
    col = client.create_collection(
        "tesla", metadata={"hnsw:space": "cosine", "embed_model": embed_model}
    )
    for i in range(0, len(docs), 500):
        col.add(
            ids=ids[i:i + 500],
            documents=docs[i:i + 500],
            metadatas=metas[i:i + 500],
            embeddings=vectors[i:i + 500],
        )
    print("Done! Database saved in chroma_db/")


if __name__ == "__main__":
    main()