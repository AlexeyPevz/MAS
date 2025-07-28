"""
chroma_store.py
===============

Простая обёртка для работы с ChromaDB. Позволяет создавать коллекции,
добавлять документы и выполнять поиск по векторам. Требует установленной
библиотеки `chromadb` и запущенного сервера Chroma.
"""

from typing import List, Optional
import os

try:
    import chromadb  # type: ignore
    from chromadb import HttpClient  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    chromadb = None  # type: ignore
    HttpClient = None  # type: ignore


class ChromaStore:
    def __init__(self, host: str | None = None, port: int | None = None) -> None:
        if chromadb is None:
            raise RuntimeError(
                "Для работы ChromaStore требуется библиотека chromadb. Установите её: pip install chromadb"
            )
        self.host = host or os.getenv("CHROMA_HOST", "localhost")
        self.port = port or int(os.getenv("CHROMA_PORT", "8000"))
        self.client = HttpClient(host=self.host, port=self.port)

    def get_or_create_collection(self, name: str):
        return self.client.get_or_create_collection(name)

    def add(
        self,
        collection_name: str,
        ids: List[str],
        documents: List[str],
        metadatas: Optional[List[dict]] = None,
    ) -> None:
        collection = self.client.get_or_create_collection(collection_name)
        collection.add(ids=ids, documents=documents, metadatas=metadatas)

    def query(
        self, collection_name: str, query_texts: List[str], n_results: int = 5
    ) -> List[dict]:
        collection = self.client.get_or_create_collection(collection_name)
        return collection.query(query_texts=query_texts, n_results=n_results)
