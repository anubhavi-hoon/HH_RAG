#!/usr/bin/env python3
"""
Embedding generation pipeline for multilingual RAG.
Project: HH Goa 2026 Voice-Enabled Multilingual RAG System.

Loads sentence-transformers/all-MiniLM-L6-v2, reads semantic chunks,
generates normalized embeddings in batches, and saves outputs to data/embeddings/.
"""

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
from sentence_transformers import SentenceTransformer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("embeddings")


def generate_embeddings(
    input_path: str,
    output_dir: str,
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    batch_size: int = 64,
    limit: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Generates normalized embeddings for JSONL text chunks.

    Args:
        input_path: Path to the input JSONL file containing chunks.
        output_dir: Directory where embeddings.npy and embedding_metadata.jsonl will be saved.
        model_name: SentenceTransformer model name.
        batch_size: Batch size for encoding.
        limit: Optional limit on the number of records to process (for smoke testing).

    Returns:
        Dict containing validation statistics and metrics.
    """
    t_start = time.time()
    input_file = Path(input_path)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found at {input_path}")

    # 1. Read input records
    logger.info(f"Reading chunks from {input_path}...")
    records: List[Dict[str, Any]] = []
    texts: List[str] = []
    
    with open(input_file, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            if limit is not None and len(records) >= limit:
                break
            record = json.loads(line)
            # Verify required fields
            if "chunk_id" not in record or "text" not in record:
                raise ValueError(
                    f"Line {idx} missing 'chunk_id' or 'text' fields: {record}"
                )
            records.append(record)
            texts.append(record["text"])

    num_records = len(records)
    logger.info(f"Loaded {num_records:,} chunks to process.")

    # 2. Load model
    logger.info(f"Loading SentenceTransformer model: {model_name}...")
    model = SentenceTransformer(model_name)

    # 3. Generate embeddings
    logger.info(f"Encoding {num_records:,} chunks with batch_size={batch_size}...")
    t_encode_start = time.time()
    
    # SentenceTransformer.encode automatically manages batches and progress tracking
    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=True,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )
    
    encode_time = time.time() - t_encode_start
    embedding_dim = embeddings.shape[1]
    dtype_name = str(embeddings.dtype)

    # Verify correct shape and type
    assert embeddings.shape == (num_records, embedding_dim), f"Expected shape {(num_records, embedding_dim)}, got {embeddings.shape}"
    assert embeddings.dtype == np.float32, f"Expected dtype float32, got {embeddings.dtype}"

    # 4. Save embeddings array
    npy_path = out_dir / "embeddings.npy"
    logger.info(f"Saving embeddings matrix to {npy_path}...")
    np.save(str(npy_path), embeddings)

    # 5. Save metadata records aligned with the embeddings matrix
    meta_path = out_dir / "embedding_metadata.jsonl"
    logger.info(f"Saving metadata to {meta_path}...")
    with open(meta_path, "w", encoding="utf-8") as f_meta:
        for idx, rec in enumerate(records):
            meta_record = {
                "embedding_index": idx,
                "chunk_id": rec["chunk_id"],
                "language": rec.get("language", ""),
                "text": rec["text"],
                # Preserve all original fields
                "parent_passage_id": rec.get("parent_passage_id", ""),
                "chunk_index": rec.get("chunk_index"),
                "chunk_strategy": rec.get("chunk_strategy", ""),
                "query_id": rec.get("query_id"),
                "is_selected": rec.get("is_selected"),
                "source": rec.get("source", ""),
            }
            f_meta.write(json.dumps(meta_record, ensure_ascii=False) + "\n")

    # 6. Validation and metrics calculation
    logger.info("Validating generated embeddings and metadata...")
    
    # Calculate norms (should be very close to 1.0 since normalize_embeddings=True)
    norms = np.linalg.norm(embeddings, axis=1)
    min_norm = float(np.min(norms))
    max_norm = float(np.max(norms))
    avg_norm = float(np.mean(norms))

    # Check for NaNs and Infs
    has_nan = bool(np.isnan(embeddings).any())
    has_inf = bool(np.isinf(embeddings).any())

    # Check chunk ID uniqueness
    chunk_ids = [rec["chunk_id"] for rec in records]
    unique_chunk_ids = len(set(chunk_ids)) == len(chunk_ids)

    # Check sequential indices
    indices_sequential = True
    metadata_count = 0
    first_aligned = False
    last_aligned = False

    # Read back metadata to verify count and alignment
    read_chunk_ids = []
    with open(meta_path, "r", encoding="utf-8") as f_meta:
        meta_lines = f_meta.readlines()
        metadata_count = len(meta_lines)
        if metadata_count > 0:
            first_meta = json.loads(meta_lines[0])
            last_meta = json.loads(meta_lines[-1])
            
            first_aligned = (first_meta["embedding_index"] == 0 and first_meta["chunk_id"] == records[0]["chunk_id"])
            last_aligned = (last_meta["embedding_index"] == num_records - 1 and last_meta["chunk_id"] == records[-1]["chunk_id"])
            
            for i, line in enumerate(meta_lines):
                meta_rec = json.loads(line)
                read_chunk_ids.append(meta_rec["chunk_id"])
                if meta_rec["embedding_index"] != i:
                    indices_sequential = False

    validation_passed = (
        not has_nan and
        not has_inf and
        unique_chunk_ids and
        metadata_count == num_records and
        indices_sequential and
        first_aligned and
        last_aligned and
        (abs(avg_norm - 1.0) < 1e-4)
    )

    elapsed_time = time.time() - t_start
    throughput = num_records / encode_time if encode_time > 0 else 0.0

    stats = {
        "model_name": model_name,
        "chunks_processed": num_records,
        "embedding_dimension": embedding_dim,
        "dtype": dtype_name,
        "batch_size": batch_size,
        "processing_time_seconds": round(elapsed_time, 2),
        "encoding_time_seconds": round(encode_time, 2),
        "embedding_throughput_fps": round(throughput, 2),
        "min_norm": round(min_norm, 5),
        "max_norm": round(max_norm, 5),
        "avg_norm": round(avg_norm, 5),
        "has_nan": has_nan,
        "has_inf": has_inf,
        "unique_chunk_ids": unique_chunk_ids,
        "metadata_count": metadata_count,
        "indices_sequential": indices_sequential,
        "first_aligned": first_aligned,
        "last_aligned": last_aligned,
        "validation_passed": validation_passed,
        "embeddings_file_size_bytes": npy_path.stat().st_size,
        "metadata_file_size_bytes": meta_path.stat().st_size,
    }

    # Print the report requested in the prompt
    print("\n" + "=" * 50)
    print("STAGE 2A EMBEDDING REPORT")
    print("=" * 50)
    print(f"Model:\n{model_name}\n")
    print(f"Input:\n{input_path}\n")
    print(f"Chunks processed:\n{num_records}\n")
    print(f"Embedding dimension:\n{embedding_dim}\n")
    print(f"dtype:\n{dtype_name}\n")
    print(f"Batch size:\n{batch_size}\n")
    print(f"Processing time:\n{elapsed_time:.2f} seconds\n")
    print(f"Embedding throughput:\n{throughput:.2f} chunks/sec\n")
    print(f"Output:\n{npy_path}\n")
    print(f"Metadata:\n{meta_path}\n")
    print(f"Validation:\n{'PASS' if validation_passed else 'FAIL'}")
    print("=" * 50 + "\n")

    return stats


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate normalized embeddings for MSMARCO-XI semantic chunks."
    )
    parser.add_argument(
        "--input",
        type=str,
        default="data/processed/chunks_semantic.jsonl",
        help="Path to semantic chunks JSONL file",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/embeddings",
        help="Directory to save generated embedding assets",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="sentence-transformers/all-MiniLM-L6-v2",
        help="SentenceTransformer model name to use",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=64,
        help="Batch size for generating embeddings",
    )
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help="Run a 100-chunk smoke test instead of full processing",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    limit_val = 100 if args.smoke_test else None
    try:
        generate_embeddings(
            input_path=args.input,
            output_dir=args.output_dir,
            model_name=args.model,
            batch_size=args.batch_size,
            limit=limit_val,
        )
    except KeyboardInterrupt:
        logger.info("Process interrupted by user. Exiting.")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}", exc_info=True)
        sys.exit(1)
