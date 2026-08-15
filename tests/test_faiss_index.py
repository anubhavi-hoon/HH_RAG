"""Unit tests for the FAISS index construction, persistence, and basic search."""

import os
import tempfile
from pathlib import Path

import faiss
import numpy as np
import pytest
from src.retrieval.faiss_index import (
    build_faiss_index,
    get_index_info,
    load_faiss_index,
)


@pytest.fixture
def temp_embeddings_file():
    """Create a temporary numpy file containing 10 mock embeddings."""
    # Create 10 vectors of dimension 384, normalized to unit length
    raw_vectors = np.random.randn(10, 384).astype(np.float32)
    norms = np.linalg.norm(raw_vectors, axis=1, keepdims=True)
    normalized_vectors = raw_vectors / norms

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        npy_file = tmp_path / "mock_embeddings.npy"
        np.save(str(npy_file), normalized_vectors)
        yield npy_file


def test_build_faiss_index(temp_embeddings_file):
    """Test index building, property detection, and persistence reloading."""
    index_path = temp_embeddings_file.parent / "embeddings.faiss"

    # 1. Build Index
    build_faiss_index(str(temp_embeddings_file), str(index_path))
    assert index_path.exists()

    # 2. Load Index
    index = load_faiss_index(str(index_path))
    assert isinstance(index, faiss.IndexFlatIP)

    # 3. Retrieve and inspect properties
    info = get_index_info(index)
    assert info["index_type"] == "IndexFlatIP"
    assert info["ntotal"] == 10
    assert info["d"] == 384
    assert info["metric"] == "Inner Product"


def test_basic_search_sanity(temp_embeddings_file):
    """Test query search on the build index and ensure correctness."""
    index_path = temp_embeddings_file.parent / "embeddings.faiss"
    build_faiss_index(str(temp_embeddings_file), str(index_path))
    
    index = load_faiss_index(str(index_path))
    embeddings = np.load(str(temp_embeddings_file))

    # Query with the 3rd vector (index 2)
    query_vector = embeddings[2:3]
    
    # Run k=3 search
    distances, indices = index.search(query_vector, 3)

    # Assert search returns correct structure
    assert distances.shape == (1, 3)
    assert indices.shape == (1, 3)

    # First result should be the query vector itself (index 2) with cosine similarity near 1.0
    assert indices[0][0] == 2
    assert pytest.approx(distances[0][0], abs=1e-4) == 1.0

    # Ensure all similarity scores and indices are finite and valid
    assert all(np.isfinite(distances[0]))
    assert all(0 <= idx < 10 for idx in indices[0])
