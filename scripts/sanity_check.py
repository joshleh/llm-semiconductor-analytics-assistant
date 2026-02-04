from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

import numpy as np
from chromadb import PersistentClient
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

from semicon_assistant.config import settings


@dataclass
class DocChunk:
    source: str
    chunk_id: int
    text: str


def ensure_sample_docs() -> List[Tuple[str, str]]:
    """
    Creates a tiny local sample corpus so the pipeline can run immediately.
    This avoids needing any real or sensitive data.
    """
    sample_dir = Path("data/sample_docs")
    sample_dir.mkdir(parents=True, exist_ok=True)

    files = [
        (
            sample_dir / "yield_notes.txt",
            "Weekly yield summary: Yield dipped on Line B after photo step adjustment. "
            "Primary excursion correlated with humidity spikes. Recommended: verify chamber seals "
            "and review SPC limits for humidity sensors.",
        ),
        (
            sample_dir / "fa_notes.txt",
            "Failure analysis notes: Open circuit observed in a subset of units. "
            "Cross-section suggests voiding near interconnect. Potential root cause: "
            "process temperature profile drift during reflow.",
        ),
        (
            sample_dir / "process_change.txt",
            "Process change log: Updated etch recipe v3.2 to reduce sidewall roughness. "
            "Observed improvement in parametric stability. Monitor for any increased defect density "
            "in the next two lots.",
        ),
    ]

    for path, content in files:
        if not path.exists():
            path.write_text(content, encoding="utf-8")

    return [(str(p), p.read_text(encoding="utf-8")) for p, _ in files]


def chunk_text(text: str, chunk_size: int, overlap: int) -> List[str]:
    text = text.strip()
    if not text:
        return []

    chunks = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + chunk_size, n)
        chunks.append(text[start:end])
        if end == n:
            break
        start = max(0, end - overlap)
    return chunks


def build_or_load_chroma_collection():
    """
    Uses ChromaDB with OpenAI embeddings.

    If OPENAI_API_KEY is missing, we still build the corpus index in a simplified way:
    - We'll skip embedding + retrieval and just print a message.
    """
    api_key = settings.openai_api_key or os.getenv("OPENAI_API_KEY")

    if not api_key:
        return None, None

    client = PersistentClient(path=settings.chroma_persist_dir)
    embed_fn = OpenAIEmbeddingFunction(
        api_key=api_key,
        model_name=settings.embedding_model,
    )

    collection = client.get_or_create_collection(
        name="semicon_sanity",
        embedding_function=embed_fn,
        metadata={"hnsw:space": "cosine"},
    )
    return client, collection


def upsert_corpus(collection, corpus: List[Tuple[str, str]]) -> List[DocChunk]:
    chunks: List[DocChunk] = []
    ids = []
    docs = []
    metadatas = []

    for source, text in corpus:
        ctexts = chunk_text(text, settings.chunk_size, settings.chunk_overlap)
        for i, c in enumerate(ctexts):
            chunk = DocChunk(source=source, chunk_id=i, text=c)
            chunks.append(chunk)
            ids.append(f"{source}::chunk{i}")
            docs.append(c)
            metadatas.append({"source": source, "chunk_id": i})

    # Chroma upsert
    if ids:
        collection.upsert(ids=ids, documents=docs, metadatas=metadatas)

    return chunks


def retrieve(collection, query: str, top_k: int) -> List[Tuple[str, str]]:
    """
    Returns a list of (source, text_chunk).
    """
    res = collection.query(query_texts=[query], n_results=top_k)
    docs = res.get("documents", [[]])[0]
    metas = res.get("metadatas", [[]])[0]

    out = []
    for d, m in zip(docs, metas):
        out.append((m.get("source", "unknown"), d))
    return out


def generate_answer(query: str, contexts: List[Tuple[str, str]]) -> str:
    """
    Uses OpenAI chat completion to answer with citations.
    If no API key, returns a fallback response.
    """
    api_key = settings.openai_api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        # Fallback: no LLM call
        lines = ["OPENAI_API_KEY not set. Showing retrieved context only (no LLM response)."]
        for i, (src, txt) in enumerate(contexts, start=1):
            lines.append(f"[{i}] {src}: {txt[:240]}{'...' if len(txt) > 240 else ''}")
        return "\n".join(lines)

    from openai import OpenAI

    client = OpenAI(api_key=api_key)

    citation_block = "\n".join([f"[{i}] {src}" for i, (src, _) in enumerate(contexts, start=1)])
    context_text = "\n\n".join(
        [f"Source [{i}] ({src}):\n{txt}" for i, (src, txt) in enumerate(contexts, start=1)]
    )

    system = (
        "You are an engineering analytics assistant for semiconductor workflows. "
        "Answer using ONLY the provided context. "
        "If the context is insufficient, say what is missing. "
        "Include citations like [1], [2] tied to the sources."
    )

    user = (
        f"Question: {query}\n\n"
        f"Available sources:\n{citation_block}\n\n"
        f"Context:\n{context_text}\n\n"
        "Respond with a concise answer and citations."
    )

    resp = client.chat.completions.create(
        model=settings.model_name,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.2,
    )
    return resp.choices[0].message.content


def main():
    print("=== Sanity Check: Minimal RAG Pipeline ===")
    print(f"Vector DB: {settings.vector_db}")
    print(f"Chroma persist dir: {settings.chroma_persist_dir}")

    corpus = ensure_sample_docs()

    client, collection = build_or_load_chroma_collection()
    if collection is None:
        print("\nOPENAI_API_KEY is not set.")
        print("To run full RAG (embeddings + retrieval + LLM), add OPENAI_API_KEY to your .env file.")
        print("For now, we will just print the sample docs.\n")
        for src, text in corpus:
            print(f"- {src}: {text[:200]}{'...' if len(text) > 200 else ''}")
        return

    # Build index
    upsert_corpus(collection, corpus)

    # Example query
    query = "What might explain the yield dip and what should we check?"
    contexts = retrieve(collection, query, settings.top_k)

    print("\n--- Retrieved Context ---")
    for i, (src, txt) in enumerate(contexts, start=1):
        print(f"\n[{i}] {src}\n{txt}")

    answer = generate_answer(query, contexts)

    print("\n--- Answer ---")
    print(answer)


if __name__ == "__main__":
    main()