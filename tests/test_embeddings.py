"""Unit tests for the embedding generation pipeline."""

import json
import tempfile
from pathlib import Path

import numpy as np
import pytest
from src.retrieval.embeddings import generate_embeddings


@pytest.fixture
def temp_chunks_jsonl():
    """Create a temporary chunks_semantic.jsonl containing 5 sample chunks."""
    sample_data = [
        {
            "chunk_id": f"doc_test_{i}",
            "parent_passage_id": "doc_parent",
            "language": "hi" if i % 2 == 0 else "en",
            "text": f"This is some sample text for testing embedding generation {i}.",
            "chunk_index": i,
            "chunk_strategy": "semantic",
            "query_id": 999,
            "is_selected": True,
            "source": "test_suite",
        }
        for i in range(5)
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        jsonl_file = tmp_path / "chunks_semantic.jsonl"
        with open(jsonl_file, "w", encoding="utf-8") as f:
            for item in sample_data:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
        yield jsonl_file


def test_generate_embeddings_pipeline(temp_chunks_jsonl):
    """Test generating embeddings for sample chunks and verify correctness."""
    output_dir = temp_chunks_jsonl.parent / "embeddings"

    # Run embedding pipeline
    stats = generate_embeddings(
        input_path=str(temp_chunks_jsonl),
        output_dir=str(output_dir),
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        batch_size=2,
    )

    # 1. Verify returned statistics structure
    assert stats["validation_passed"] is True
    assert stats["chunks_processed"] == 5
    assert stats["embedding_dimension"] == 384
    assert stats["dtype"] == "float32"
    assert stats["has_nan"] is False
    assert stats["has_inf"] is False
    assert stats["unique_chunk_ids"] is True
    assert stats["metadata_count"] == 5
    assert stats["indices_sequential"] is True
    assert stats["first_aligned"] is True
    assert stats["last_aligned"] is True

    # 2. Load generated array and check properties
    npy_file = output_dir / "embeddings.npy"
    assert npy_file.exists()
    embeddings = np.load(str(npy_file))
    
    assert embeddings.shape == (5, 384)
    assert embeddings.dtype == np.float32

    # Check that embeddings are normalized (norm should be ~1.0)
    norms = np.linalg.norm(embeddings, axis=1)
    for norm in norms:
        assert pytest.approx(norm, abs=1e-4) == 1.0

    # 3. Load generated metadata and check alignment
    meta_file = output_dir / "embedding_metadata.jsonl"
    assert meta_file.exists()

    with open(meta_file, "r", encoding="utf-8") as f:
        meta_lines = [json.loads(line) for line in f]

    assert len(meta_lines) == 5
    for idx, item in enumerate(meta_lines):
        assert item["embedding_index"] == idx
        assert item["chunk_id"] == f"doc_test_{idx}"
        assert item["text"] == f"This is some sample text for testing embedding generation {idx}."
