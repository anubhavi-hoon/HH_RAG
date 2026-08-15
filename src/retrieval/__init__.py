"""Retrieval package containing the embedding pipeline and index helpers."""

from src.retrieval.embeddings import generate_embeddings
from src.retrieval.faiss_index import (
    build_faiss_index,
    load_faiss_index,
    get_index_info,
)
from src.retrieval.retriever import retrieve_chunks

__all__ = [
    "generate_embeddings",
    "build_faiss_index",
    "load_faiss_index",
    "get_index_info",
    "retrieve_chunks",
]
