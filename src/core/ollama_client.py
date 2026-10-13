
import os
from typing import Any

import httpx


OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_BASE_URL",
    "http://host.docker.internal:11434",
).rstrip("/")

LLM_MODEL = os.getenv("LLM_MODEL", "qwen2.5:7b")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "bge-m3:latest")

EMBEDDING_DIMENSION = 1024


async def embed_texts(texts: list[str]) -> list[list[float]]:
    """Matnlarni BGE-M3 orqali 1024 o'lchamli vektorlarga aylantiradi."""
    if not texts:
        return []

    async with httpx.AsyncClient(
        base_url=OLLAMA_BASE_URL,
        timeout=httpx.Timeout(180.0, connect=10.0),
    ) as client:
        response = await client.post(
            "/api/embed",
            json={
                "model": EMBEDDING_MODEL,
                "input": texts,
            },
        )
        response.raise_for_status()
        data: dict[str, Any] = response.json()

    embeddings = data.get("embeddings", [])

    if len(embeddings) != len(texts):
        raise RuntimeError(
            f"Embedding soni mos emas: "
            f"{len(embeddings)} ta matn, {len(embeddings)} ta vektor."
        )

    for index, vector in enumerate(embeddings):
        if len(vector) != EMBEDDING_DIMENSION:
            raise RuntimeError(
                f"{index}-vektor o'lchami {len(vector)}; "
                f"kutilgan o'lcham {EMBEDDING_DIMENSION}."
            )

    return embeddings


async def generate_answer(
    messages: list[dict[str, str]],
    temperature: float = 0.2,
) -> str:
    """Ollama chat API orqali javob oladi."""
    async with httpx.AsyncClient(
        base_url=OLLAMA_BASE_URL,
        timeout=httpx.Timeout(300.0, connect=10.0),
    ) as client:
        response = await client.post(
            "/api/chat",
            json={
                "model": LLM_MODEL,
                "messages": messages,
                "stream": False,
                "options": {"temperature": temperature},
            },
        )
        response.raise_for_status()
        data = response.json()

    answer = data.get("message", {}).get("content", "").strip()

    if not answer:
        raise RuntimeError("Ollama bo'sh javob qaytardi.")

    return answer
