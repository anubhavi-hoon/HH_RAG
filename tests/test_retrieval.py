"""Unit tests for the production retrieval module."""

import pytest
from tqdm import tqdm
tqdm.monitor_interval = 0

from src.retrieval.retriever import retrieve_chunks, get_index, get_metadata



def test_successful_english_retrieval():
    """Verify that retrieval works for an English query and returns correct fields."""
    res = retrieve_chunks("Manhattan Project atomic bomb history", top_k=5)
    
    assert len(res) == 5
    for rank, item in enumerate(res, start=1):
        assert item["rank"] == rank
        assert isinstance(item["chunk_id"], str)
        assert isinstance(item["text"], str)
        assert isinstance(item["language"], str)
        assert isinstance(item["score"], float)
        assert -1.0 <= item["score"] <= 1.0
        
        # Verify specific fields from the original metadata are preserved
        assert "parent_passage_id" in item
        assert "chunk_index" in item
        assert "chunk_strategy" in item
        assert "query_id" in item
        assert "is_selected" in item
        assert "source" in item




def test_successful_hindi_retrieval():
    """Verify that retrieval works for a Hindi query."""
    res = retrieve_chunks("परमाणु ऊर्जा का शांतिपूर्ण उपयोग इतिहास", top_k=3)
    assert len(res) == 3
    for item in res:
        assert isinstance(item["chunk_id"], str)
        assert isinstance(item["text"], str)
        assert isinstance(item["score"], float)


def test_result_ordering():
    """Verify results are returned in descending similarity score order."""
    res = retrieve_chunks("scientific intellect and communication", top_k=5)
    scores = [item["score"] for item in res]
    # Check sorted descending
    assert scores == sorted(scores, reverse=True)


def test_empty_and_whitespace_queries():
    """Verify empty or whitespace-only queries raise ValueError."""
    with pytest.raises(ValueError, match="Query cannot be empty or whitespace-only"):
        retrieve_chunks("")

    with pytest.raises(ValueError, match="Query cannot be empty or whitespace-only"):
        retrieve_chunks("   ")

    with pytest.raises(ValueError, match="Query must be a string"):
        retrieve_chunks(None)


def test_invalid_top_k():
    """Verify invalid top_k parameters raise ValueError."""
    with pytest.raises(ValueError, match="top_k must be a positive integer"):
        retrieve_chunks("query text", top_k=0)

    with pytest.raises(ValueError, match="top_k must be a positive integer"):
        retrieve_chunks("query text", top_k=-5)

    with pytest.raises(ValueError, match="top_k must be a positive integer"):
        retrieve_chunks("query text", top_k=2.5)


def test_top_k_clamping():
    """Verify that top_k is clamped to index.ntotal if it exceeds it."""
    index = get_index()
    excessive_k = index.ntotal + 100
    res = retrieve_chunks("some search query", top_k=excessive_k)
    assert len(res) == index.ntotal


def test_index_and_metadata_consistency():
    """Verify in-memory consistency between index and metadata files."""
    index = get_index()
    metadata = get_metadata()
    assert index.ntotal == len(metadata)
    assert index.d == 384
