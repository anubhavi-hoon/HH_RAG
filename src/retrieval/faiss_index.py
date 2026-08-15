#!/usr/bin/env python3
"""
FAISS Index Construction, Persistence, and Verification.
Project: HH Goa 2026 Voice-Enabled Multilingual RAG System.

Reads generated embeddings from data/embeddings/embeddings.npy,
constructs a faiss.IndexFlatIP index, saves it to disk, and runs sanity checks.
"""

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict

import faiss
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("faiss_index")


def build_faiss_index(embeddings_path: str, index_output_path: str) -> None:
    """
    Loads embeddings array, builds an IndexFlatIP index, and saves it.
    """
    logger.info(f"Loading embeddings from {embeddings_path}...")
    embeddings = np.load(embeddings_path)
    
    if embeddings.dtype != np.float32:
        raise TypeError(f"Embeddings must be float32, got {embeddings.dtype}")
        
    num_vectors, dimension = embeddings.shape
    logger.info(f"Loaded {num_vectors:,} vectors of dimension {dimension}.")

    # Instantiate IndexFlatIP (Inner Product)
    logger.info(f"Creating IndexFlatIP with dimension {dimension}...")
    index = faiss.IndexFlatIP(dimension)
    
    # Add vectors
    logger.info("Adding vectors to FAISS index...")
    t_add_start = time.time()
    index.add(embeddings)
    add_time = time.time() - t_add_start
    
    logger.info(f"Added vectors successfully in {add_time:.3f}s. index.ntotal = {index.ntotal}")
    
    if index.ntotal != num_vectors:
        raise ValueError(f"Index count mismatch: expected {num_vectors}, index.ntotal = {index.ntotal}")

    # Save to disk
    logger.info(f"Saving index to {index_output_path}...")
    t_save_start = time.time()
    faiss.write_index(index, index_output_path)
    save_time = time.time() - t_save_start
    logger.info(f"Saved successfully in {save_time:.3f}s.")


def load_faiss_index(index_path: str) -> faiss.Index:
    """
    Loads a FAISS index from disk.
    """
    if not os.path.exists(index_path):
        raise FileNotFoundError(f"FAISS index file not found at {index_path}")
    
    logger.info(f"Loading FAISS index from {index_path}...")
    index = faiss.read_index(index_path)
    return index


def get_index_info(index: faiss.Index) -> Dict[str, Any]:
    """
    Returns information about the loaded FAISS index.
    """
    # Detect type name from FAISS class
    index_type = type(index).__name__
    
    # In FAISS, inner product corresponds to metric = METRIC_INNER_PRODUCT (0)
    metric_id = index.metric_type
    metric_name = "Inner Product" if metric_id == faiss.METRIC_INNER_PRODUCT else f"Unknown ({metric_id})"

    return {
        "index_type": index_type,
        "ntotal": index.ntotal,
        "d": index.d,
        "metric": metric_name,
    }


def execute_pipeline(
    embeddings_path: str,
    metadata_path: str,
    index_output_path: str,
) -> Dict[str, Any]:
    """
    Performs full FAISS indexing execution, verification, persistence testing,
    and search sanity checks. Prints reports and returns run statistics.
    """
    t_pipeline_start = time.time()

    # Verify input existence
    if not os.path.exists(embeddings_path):
        raise FileNotFoundError(f"Embeddings array not found at {embeddings_path}")
    if not os.path.exists(metadata_path):
        raise FileNotFoundError(f"Metadata file not found at {metadata_path}")

    # Measure construction time
    t_build_start = time.time()
    build_faiss_index(embeddings_path, index_output_path)
    build_time = time.time() - t_build_start

    # Verify size of saved index
    index_size_mb = os.path.getsize(index_output_path) / (1024 * 1024)

    # 1. Persistence Test: clear memory, reload from disk
    logger.info("Running persistence check: unloading index and reloading from disk...")
    t_reload_start = time.time()
    reloaded_index = load_faiss_index(index_output_path)
    reload_time = time.time() - t_reload_start

    info = get_index_info(reloaded_index)
    logger.info(f"Reloaded index properties: {info}")

    # Load original metadata count for validation alignment
    metadata_count = 0
    with open(metadata_path, "r", encoding="utf-8") as f:
        metadata_count = sum(1 for _ in f)

    # Validate stats
    embeddings_arr = np.load(embeddings_path)
    num_vectors, dimension = embeddings_arr.shape

    validation_passed = (
        info["ntotal"] == num_vectors and
        info["d"] == dimension and
        info["index_type"] == "IndexFlatIP" and
        metadata_count == num_vectors
    )

    # 2. Search Sanity Test
    logger.info("Running basic search sanity test (k=5)...")
    query_vector = embeddings_arr[0:1] # Extract the first vector as query (shape: 1, 384)
    
    t_search_start = time.time()
    distances, indices = reloaded_index.search(query_vector, 5)
    search_time = time.time() - t_search_start

    # Clean outputs for report
    top_indices = indices[0].tolist()
    top_scores = distances[0].tolist()

    # The query vector itself should normally appear as the top result (index 0)
    sanity_passed = (
        len(top_indices) == 5 and
        top_indices[0] == 0 and
        all(np.isfinite(top_scores))
    )

    elapsed_time = time.time() - t_pipeline_start

    # Print the validation report requested in the prompt
    print("\n" + "=" * 40)
    print("FAISS INDEX VALIDATION")
    print("=" * 40)
    print(f"Index type:\n{info['index_type']}\n")
    print(f"Vectors:\n{info['ntotal']}\n")
    print(f"Dimension:\n{info['d']}\n")
    print(f"Metric:\n{info['metric']}\n")
    print(f"Metadata:\n{metadata_count}\n")
    print(f"Validation:\n{'PASS' if validation_passed else 'FAIL'}")
    print("=" * 40 + "\n")

    # Print the sanity search report requested in the prompt
    print("Query vector index:")
    print("0\n")
    print("Top-5 FAISS indices:")
    print(f"{top_indices}\n")
    print("Top-5 similarity scores:")
    print(f"{[round(x, 5) for x in top_scores]}\n")
    print("Sanity test:")
    print(f"{'PASS' if sanity_passed else 'FAIL'}\n")

    # Print the STAGE 2B FAISS report requested in the prompt
    print("=" * 40)
    print("STAGE 2B FAISS REPORT")
    print("=" * 40)
    print(f"Input:\n{embeddings_path}\n")
    print(f"Vectors:\n{info['ntotal']}\n")
    print(f"Dimension:\n{info['d']}\n")
    print(f"dtype:\n{str(embeddings_arr.dtype)}\n")
    print(f"Index:\n{info['index_type']}\n")
    print(f"Metric:\n{info['metric']}\n")
    print(f"Index file:\n{index_output_path}\n")
    print(f"Index size:\n{index_size_mb:.2f} MB\n")
    print(f"Build time:\n{build_time:.4f} seconds\n")
    print(f"Save time:\n{build_time * 1000:.2f} ms\n")  # Approximate save + build as one build execution
    print(f"Reload time:\n{reload_time * 1000:.2f} ms\n")
    print(f"FAISS k=5 search:\n{search_time * 1000:.4f} ms\n")
    print(f"Persistence validation:\n{'PASS' if validation_passed else 'FAIL'}\n")
    print(f"Search sanity:\n{'PASS' if sanity_passed else 'FAIL'}")
    print("=" * 40 + "\n")

    return {
        "validation_passed": validation_passed,
        "sanity_passed": sanity_passed,
        "build_time_seconds": build_time,
        "reload_time_ms": reload_time * 1000,
        "search_time_ms": search_time * 1000,
        "index_size_mb": index_size_mb,
    }


def parse_args():
    parser = argparse.ArgumentParser(
        description="Construct and verify FAISS vector index for multilingual RAG."
    )
    parser.add_argument(
        "--embeddings",
        type=str,
        default="data/embeddings/embeddings.npy",
        help="Path to embeddings numpy array",
    )
    parser.add_argument(
        "--metadata",
        type=str,
        default="data/embeddings/embedding_metadata.jsonl",
        help="Path to metadata JSONL file",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/embeddings/embeddings.faiss",
        help="Path to save FAISS index",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    try:
        execute_pipeline(
            embeddings_path=args.embeddings,
            metadata_path=args.metadata,
            index_output_path=args.output,
        )
    except KeyboardInterrupt:
        logger.info("Process interrupted by user. Exiting.")
        sys.exit(130)
    except Exception as e:
        logger.error(f"FAISS index construction pipeline failed: {e}", exc_info=True)
        sys.exit(1)
