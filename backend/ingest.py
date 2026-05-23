"""
ingest.py — One-time script to build the ChromaDB vector store from knowledge docs.

Run once before starting the server:
    python backend/ingest.py

Re-run whenever knowledge documents are updated.
"""

from pathlib import Path
from sentence_transformers import SentenceTransformer
import chromadb

BASE_DIR = Path(__file__).resolve().parent
KNOWLEDGE_DIR = BASE_DIR / "knowledge"
DB_DIR = BASE_DIR / "chroma_db"
COLLECTION_NAME = "it_knowledge"

# Target characters per chunk
CHUNK_TARGET = 500


def chunk_by_section(text: str) -> list[str]:
    """
    Split a markdown document into chunks by heading sections.
    Each ### or ## heading starts a new chunk. Chunks that grow beyond
    CHUNK_TARGET are split further at paragraph boundaries.
    """
    lines = text.splitlines(keepends=True)
    sections: list[str] = []
    current: list[str] = []

    for line in lines:
        if line.startswith("##") and current:
            sections.append("".join(current).strip())
            current = [line]
        else:
            current.append(line)

    if current:
        sections.append("".join(current).strip())

    # Split sections that are still too long at paragraph breaks
    chunks: list[str] = []
    for section in sections:
        if not section:
            continue
        if len(section) <= CHUNK_TARGET:
            chunks.append(section)
        else:
            paras = [p.strip() for p in section.split("\n\n") if p.strip()]
            bucket = ""
            for para in paras:
                candidate = (bucket + "\n\n" + para).strip() if bucket else para
                if len(candidate) <= CHUNK_TARGET:
                    bucket = candidate
                else:
                    if bucket:
                        chunks.append(bucket)
                    bucket = para
            if bucket:
                chunks.append(bucket)

    return [c for c in chunks if len(c) > 40]  # drop trivial fragments


def ingest():
    md_files = list(KNOWLEDGE_DIR.glob("*.md"))
    if not md_files:
        print(f"[Ingest] No markdown files found in {KNOWLEDGE_DIR}")
        return

    print(f"[Ingest] Loading embedding model (all-MiniLM-L6-v2)...")
    model = SentenceTransformer("all-MiniLM-L6-v2")

    print(f"[Ingest] Connecting to ChromaDB at {DB_DIR}...")
    DB_DIR.mkdir(parents=True, exist_ok=True)
    chroma = chromadb.PersistentClient(path=str(DB_DIR))

    # Fresh collection every ingest run
    try:
        chroma.delete_collection(COLLECTION_NAME)
        print(f"[Ingest] Deleted existing collection '{COLLECTION_NAME}'")
    except Exception:
        pass

    collection = chroma.create_collection(
        COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )

    all_texts, all_ids, all_meta = [], [], []

    for md_file in sorted(md_files):
        topic = md_file.stem
        text = md_file.read_text(encoding="utf-8")
        chunks = chunk_by_section(text)

        print(f"[Ingest]   {md_file.name}: {len(chunks)} chunks")
        for i, chunk in enumerate(chunks):
            all_texts.append(chunk)
            all_ids.append(f"{topic}_{i}")
            all_meta.append({"topic": topic, "source": md_file.name, "chunk": i})

    if not all_texts:
        print("[Ingest] No chunks produced — check document formatting.")
        return

    print(f"[Ingest] Embedding {len(all_texts)} chunks...")
    embeddings = model.encode(all_texts, show_progress_bar=True).tolist()

    collection.add(
        documents=all_texts,
        embeddings=embeddings,
        ids=all_ids,
        metadatas=all_meta
    )

    print(f"\n[Ingest] Done. {len(all_texts)} chunks stored in ChromaDB.")
    print(f"[Ingest] Topics: {sorted({m['topic'] for m in all_meta})}")


if __name__ == "__main__":
    ingest()
