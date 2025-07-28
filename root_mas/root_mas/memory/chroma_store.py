"""
chroma_store.py
===============

Заглушка для работы с ChromaDB. Этот модуль представляет интерфейс для
создания коллекций и добавления/извлечения документов. Для использования
необходимо установить библиотеку `chromadb` и запустить сервер Chroma.
"""

from typing import List, Optional

try:
    import chromadb  # type: ignore
    from chromadb import Client  # type: ignore
except ImportError:
    chromadb = None  # type: ignore
    Client = None  # type: ignore


class ChromaStore:
    def __init__(self, host: str = "localhost", port: int = 8000):
        if chromadb is None:
            raise RuntimeError(
                "Для работы ChromaStore требуется библиотека chromadb. Установите её: pip install chromadb"
            )
        self.client = Client(host=host, port=port)

    def get_or_create_collection(self, name: str):
        return self.client.get_or_create_collection(name)

    def add(self, collection_name: str, ids: List[str], documents: List[str], metadatas: Optional[List[dict]] = None) -> None:
        collection = self.client.get_or_create_collection(collection_name)
        collection.add(ids=ids, documents=documents, metadatas=metadatas)

    def query(self, collection_name: str, query_texts: List[str], n_results: int = 5) -> List[dict]:
        collection = self.client.get_or_create_collection(collection_name)
        return collection.query(query_texts=query_texts, n_results=n_results)