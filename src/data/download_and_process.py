#!/usr/bin/env python3
"""
MSMARCO-XI Multilingual Dataset Download, Extraction, and Chunking Pipeline.
Project: HH Goa 2026 Voice-Enabled Multilingual RAG System.

Downloads the Hindi parquet file from ai4bharat/MSMARCO-XI via huggingface_hub
(cached after first download), extracts balanced English and Hindi passages,
applies fixed-size and sentence-aware chunking, and saves processed artifacts
to data/processed/.

Architecture note: The source parquet file has a SINGLE row group with 778K rows.
This means PyArrow must read entire column chunks before yielding any rows.
The fastest reliable approach is to download the file once (huggingface_hub caches
it at ~/.cache/huggingface/) and then read locally with pyarrow.
"""

import argparse
import json
import logging
import os
import re
import shutil
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

import certifi
from tqdm import tqdm

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("download_and_process")

# Set SSL Certificate file from certifi to avoid macOS SSL verification failures
os.environ.setdefault("SSL_CERT_FILE", certifi.where())
os.environ.setdefault("REQUESTS_CA_BUNDLE", certifi.where())

# Constants
DEFAULT_DATASET = "ai4bharat/MSMARCO-XI"
DEFAULT_CONFIG = "hi"
DEFAULT_SPLIT = "train"
PARQUET_FILENAME = "train/hintrain.parquet"
MAX_STORAGE_MB_WARN = 500.0


# ==========================================
# 1. Dataset Download & Record Streaming
# ==========================================

def download_and_stream_records(
    max_records: int = 5000,
) -> list:
    """
    Downloads the Hindi parquet file from HuggingFace Hub (cached after first
    download) and reads the first max_records rows using pyarrow.

    Returns:
        List of dicts, each representing one query record.
    """
    import pyarrow.parquet as pq
    from huggingface_hub import hf_hub_download

    logger.info(
        f"Downloading dataset file: {DEFAULT_DATASET} / {PARQUET_FILENAME}"
    )
    logger.info(
        "First download is ~3.5 GB and takes 5-15 minutes depending on network. "
        "Subsequent runs use cached file and are instant."
    )

    t_dl = time.time()
    local_path = hf_hub_download(
        repo_id=DEFAULT_DATASET,
        filename=PARQUET_FILENAME,
        repo_type="dataset",
    )
    dl_elapsed = time.time() - t_dl
    logger.info(f"File available at: {local_path} (resolved in {dl_elapsed:.1f}s)")

    # Read only the columns we need, and only the first max_records rows
    logger.info(f"Reading first {max_records:,} rows from local parquet file...")
    t_read = time.time()

    columns = [
        "query_id", "query", "Answer", "query_type",
        "Eng_Query", "Eng_Answer", "passages",
        "source_lang", "target_lang",
    ]

    pf = pq.ParquetFile(local_path)
    records = []
    for batch in pf.iter_batches(batch_size=500, columns=columns):
        rows = batch.to_pylist()
        records.extend(rows)
        if len(records) >= max_records:
            records = records[:max_records]
            break

    read_elapsed = time.time() - t_read
    logger.info(
        f"Read {len(records):,} records in {read_elapsed:.1f}s"
    )

    return records


# ==========================================
# 2. Chunking Strategies
# ==========================================

def chunk_fixed_size(
    text: str,
    parent_passage_id: str,
    language: str,
    query_id: Any,
    is_selected: bool,
    source: str = DEFAULT_DATASET,
    chunk_size: int = 1000,
    overlap: int = 150,
) -> List[Dict[str, Any]]:
    """
    Fixed-size character chunking with overlap.
    Preserves Unicode, avoids infinite loops, and excludes empty chunks.
    """
    text = text.strip()
    if not text:
        return []

    # Safe step size to prevent infinite loops
    step = max(1, chunk_size - overlap)
    chunks = []
    chunk_idx = 0
    start = 0
    text_len = len(text)

    while start < text_len:
        end = min(start + chunk_size, text_len)
        chunk_text = text[start:end].strip()

        if chunk_text:
            chunk_id = f"{parent_passage_id}_fixed_{chunk_idx}"
            chunks.append({
                "chunk_id": chunk_id,
                "parent_passage_id": parent_passage_id,
                "language": language,
                "text": chunk_text,
                "chunk_index": chunk_idx,
                "chunk_strategy": "fixed",
                "query_id": query_id,
                "is_selected": is_selected,
                "source": source,
            })
            chunk_idx += 1

        if end >= text_len:
            break
        start += step

    return chunks


def split_sentences_multilingual(text: str) -> List[str]:
    """
    Splits multilingual text into sentences using standard and Indic boundary punctuation:
    . ! ? । (danda) \n
    """
    # Regex splits on sentence endings followed by whitespace or linebreaks
    pattern = r"(?<=[.!?।\n])\s+"
    raw_sentences = re.split(pattern, text)
    sentences = [s.strip() for s in raw_sentences if s.strip()]
    return sentences if sentences else ([text.strip()] if text.strip() else [])


def chunk_semantic_sentence_aware(
    text: str,
    parent_passage_id: str,
    language: str,
    query_id: Any,
    is_selected: bool,
    source: str = DEFAULT_DATASET,
    max_chunk_size: int = 1200,
) -> List[Dict[str, Any]]:
    """
    Sentence-aware semantic chunking.
    Accumulates complete sentences up to max_chunk_size characters.
    If an individual sentence exceeds max_chunk_size, safely splits it with fixed-size fallback.
    """
    text = text.strip()
    if not text:
        return []

    sentences = split_sentences_multilingual(text)
    chunks = []
    chunk_idx = 0
    current_sentences: List[str] = []
    current_length = 0

    def _flush_current():
        nonlocal chunk_idx, current_sentences, current_length
        if current_sentences:
            chunk_text = " ".join(current_sentences).strip()
            if chunk_text:
                chunks.append({
                    "chunk_id": f"{parent_passage_id}_semantic_{chunk_idx}",
                    "parent_passage_id": parent_passage_id,
                    "language": language,
                    "text": chunk_text,
                    "chunk_index": chunk_idx,
                    "chunk_strategy": "semantic",
                    "query_id": query_id,
                    "is_selected": is_selected,
                    "source": source,
                })
                chunk_idx += 1
            current_sentences = []
            current_length = 0

    for sent in sentences:
        sent = sent.strip()
        if not sent:
            continue

        sent_len = len(sent)

        # Fallback for oversized single sentence
        if sent_len > max_chunk_size:
            _flush_current()
            sub_chunks = chunk_fixed_size(
                text=sent,
                parent_passage_id=parent_passage_id,
                language=language,
                query_id=query_id,
                is_selected=is_selected,
                source=source,
                chunk_size=max_chunk_size,
                overlap=100,
            )
            for sc in sub_chunks:
                sc["chunk_id"] = f"{parent_passage_id}_semantic_{chunk_idx}"
                sc["chunk_strategy"] = "semantic"
                sc["chunk_index"] = chunk_idx
                chunks.append(sc)
                chunk_idx += 1
            continue

        # Check if adding sentence exceeds max_chunk_size
        additional_len = sent_len + (1 if current_sentences else 0)
        if current_length + additional_len > max_chunk_size:
            _flush_current()

        current_sentences.append(sent)
        current_length += additional_len

    _flush_current()
    return chunks


# ==========================================
# 3. Main Extraction & Processing Pipeline
# ==========================================

def run_pipeline(
    target_passages: int = 15000,
    fixed_size: int = 1000,
    overlap: int = 150,
    semantic_size: int = 1200,
    output_dir: str = "data/processed",
    seed: int = 42,
) -> Dict[str, Any]:
    """
    Executes the balanced extraction and chunking pipeline.
    """
    t_start = time.time()
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    # Check available disk space
    try:
        free_bytes = shutil.disk_usage(out_path.resolve()).free
        free_mb = free_bytes / (1024 * 1024)
        logger.info(f"Available disk space: {free_mb:.1f} MB")
        if free_mb < 4000:
            logger.warning(
                f"LOW DISK SPACE WARNING: Only {free_mb:.1f} MB free. "
                "Need ~3.5 GB for cached download + ~50 MB for output."
            )
    except Exception as e:
        logger.warning(f"Could not check disk usage: {e}")

    # Calculate targets for balanced sampling (~50% English, ~50% Hindi)
    target_en = target_passages // 2
    target_hi = target_passages - target_en
    logger.info(f"Target Passages: {target_passages:,} (English: {target_en:,}, Hindi: {target_hi:,})")

    # Estimated queries needed (~10 passages per query, with safety margin)
    estimated_queries = int(max(50, (target_passages / 10) * 1.5))

    # Download and read records
    records = download_and_stream_records(max_records=estimated_queries)

    # Output file paths
    src_file = out_path / "source_passages.jsonl"
    fixed_file = out_path / "chunks_fixed.jsonl"
    semantic_file = out_path / "chunks_semantic.jsonl"
    stats_file = out_path / "processing_stats.json"

    # Tracking metrics
    en_collected = 0
    hi_collected = 0
    total_fixed_chunks = 0
    total_semantic_chunks = 0
    skipped_records = 0
    seen_passage_ids = set()

    # Open output JSONL files
    with open(src_file, "w", encoding="utf-8") as f_src, \
         open(fixed_file, "w", encoding="utf-8") as f_fix, \
         open(semantic_file, "w", encoding="utf-8") as f_sem:

        pbar = tqdm(total=target_passages, desc="Extracting Passages", unit="psg")

        for record in records:
            if en_collected >= target_en and hi_collected >= target_hi:
                break

            query_id = record.get("query_id", "")
            query = record.get("query", "")
            eng_query = record.get("Eng_Query", query)
            answer = record.get("Answer", "")
            eng_answer = record.get("Eng_Answer", answer)
            query_type = record.get("query_type", "")
            source_lang = record.get("source_lang", "en")
            target_lang = record.get("target_lang", "hi")

            passages_data = record.get("passages", {})
            en_passages = passages_data.get("English_passages", [])
            hi_passages = passages_data.get("Translated_passages", [])
            is_selected_list = passages_data.get("is_selected", [])

            if not en_passages and not hi_passages:
                skipped_records += 1
                continue

            num_p = max(len(en_passages), len(hi_passages))

            for idx in range(num_p):
                # 1. Process English Passage
                if en_collected < target_en and idx < len(en_passages):
                    text_en = (en_passages[idx] or "").strip()
                    if text_en:
                        p_id = f"msmarco_hi_{query_id}_en_{idx}"
                        if p_id not in seen_passage_ids:
                            seen_passage_ids.add(p_id)
                            is_sel = bool(is_selected_list[idx]) if idx < len(is_selected_list) else False

                            src_rec = {
                                "chunk_source_id": p_id,
                                "language": "en",
                                "text": text_en,
                                "query_id": query_id,
                                "query": eng_query or query,
                                "answer": eng_answer or answer,
                                "query_type": query_type,
                                "passage_index": idx,
                                "is_selected": is_sel,
                                "source_lang": source_lang,
                                "target_lang": target_lang,
                                "source": DEFAULT_DATASET,
                            }
                            f_src.write(json.dumps(src_rec, ensure_ascii=False) + "\n")
                            en_collected += 1
                            pbar.update(1)

                            # Fixed chunking
                            fix_chunks = chunk_fixed_size(
                                text=text_en,
                                parent_passage_id=p_id,
                                language="en",
                                query_id=query_id,
                                is_selected=is_sel,
                                source=DEFAULT_DATASET,
                                chunk_size=fixed_size,
                                overlap=overlap,
                            )
                            for c in fix_chunks:
                                f_fix.write(json.dumps(c, ensure_ascii=False) + "\n")
                            total_fixed_chunks += len(fix_chunks)

                            # Semantic chunking
                            sem_chunks = chunk_semantic_sentence_aware(
                                text=text_en,
                                parent_passage_id=p_id,
                                language="en",
                                query_id=query_id,
                                is_selected=is_sel,
                                source=DEFAULT_DATASET,
                                max_chunk_size=semantic_size,
                            )
                            for c in sem_chunks:
                                f_sem.write(json.dumps(c, ensure_ascii=False) + "\n")
                            total_semantic_chunks += len(sem_chunks)
                    else:
                        skipped_records += 1

                # 2. Process Hindi Passage
                if hi_collected < target_hi and idx < len(hi_passages):
                    text_hi = (hi_passages[idx] or "").strip()
                    if text_hi:
                        p_id = f"msmarco_hi_{query_id}_hi_{idx}"
                        if p_id not in seen_passage_ids:
                            seen_passage_ids.add(p_id)
                            is_sel = bool(is_selected_list[idx]) if idx < len(is_selected_list) else False

                            src_rec = {
                                "chunk_source_id": p_id,
                                "language": "hi",
                                "text": text_hi,
                                "query_id": query_id,
                                "query": query,
                                "answer": answer,
                                "query_type": query_type,
                                "passage_index": idx,
                                "is_selected": is_sel,
                                "source_lang": source_lang,
                                "target_lang": target_lang,
                                "source": DEFAULT_DATASET,
                            }
                            f_src.write(json.dumps(src_rec, ensure_ascii=False) + "\n")
                            hi_collected += 1
                            pbar.update(1)

                            # Fixed chunking
                            fix_chunks = chunk_fixed_size(
                                text=text_hi,
                                parent_passage_id=p_id,
                                language="hi",
                                query_id=query_id,
                                is_selected=is_sel,
                                source=DEFAULT_DATASET,
                                chunk_size=fixed_size,
                                overlap=overlap,
                            )
                            for c in fix_chunks:
                                f_fix.write(json.dumps(c, ensure_ascii=False) + "\n")
                            total_fixed_chunks += len(fix_chunks)

                            # Semantic chunking
                            sem_chunks = chunk_semantic_sentence_aware(
                                text=text_hi,
                                parent_passage_id=p_id,
                                language="hi",
                                query_id=query_id,
                                is_selected=is_sel,
                                source=DEFAULT_DATASET,
                                max_chunk_size=semantic_size,
                            )
                            for c in sem_chunks:
                                f_sem.write(json.dumps(c, ensure_ascii=False) + "\n")
                            total_semantic_chunks += len(sem_chunks)
                    else:
                        skipped_records += 1

                if en_collected >= target_en and hi_collected >= target_hi:
                    break

        pbar.close()

    elapsed_time = time.time() - t_start
    total_source_passages = en_collected + hi_collected

    # Calculate file sizes
    file_stats = {}
    total_bytes = 0
    for file_p in [src_file, fixed_file, semantic_file]:
        if file_p.exists():
            sz = file_p.stat().st_size
            total_bytes += sz
            file_stats[file_p.name] = {
                "size_bytes": sz,
                "size_mb": round(sz / (1024 * 1024), 3),
            }

    total_processed_mb = round(total_bytes / (1024 * 1024), 3)

    # Save processing_stats.json
    stats_data = {
        "dataset": DEFAULT_DATASET,
        "configuration": DEFAULT_CONFIG,
        "split": DEFAULT_SPLIT,
        "total_source_passages": total_source_passages,
        "english_passages": en_collected,
        "hindi_passages": hi_collected,
        "fixed_chunks": total_fixed_chunks,
        "semantic_chunks": total_semantic_chunks,
        "skipped_records": skipped_records,
        "processing_time_seconds": round(elapsed_time, 2),
        "total_processed_size_mb": total_processed_mb,
        "files": file_stats,
        "parameters": {
            "target_passages": target_passages,
            "fixed_size": fixed_size,
            "overlap": overlap,
            "semantic_size": semantic_size,
            "seed": seed,
        },
    }

    with open(stats_file, "w", encoding="utf-8") as f:
        json.dump(stats_data, f, ensure_ascii=False, indent=2)

    # Check 500MB storage limit
    if total_processed_mb > MAX_STORAGE_MB_WARN:
        logger.warning(f"STORAGE WARNING: Total processed data ({total_processed_mb} MB) exceeds {MAX_STORAGE_MB_WARN} MB limit!")
    else:
        logger.info(f"Storage safety check passed: Total processed size {total_processed_mb} MB is comfortably below {MAX_STORAGE_MB_WARN} MB.")

    # Print summary
    print("\n" + "=" * 50)
    print("PROCESSING COMPLETE")
    print("=" * 50)
    print(f"Source passages: {total_source_passages:,}")
    print(f"English passages: {en_collected:,}")
    print(f"Hindi passages: {hi_collected:,}")
    print(f"Fixed chunks: {total_fixed_chunks:,}")
    print(f"Semantic chunks: {total_semantic_chunks:,}")
    print(f"Skipped records: {skipped_records:,}")
    print(f"Total processed data size: {total_processed_mb} MB")
    print(f"Processing time: {elapsed_time:.2f} seconds")
    print("=" * 50 + "\n")

    return stats_data


# ==========================================
# 4. CLI Interface
# ==========================================

def parse_args():
    parser = argparse.ArgumentParser(
        description="Download, normalize, and chunk MSMARCO-XI dataset for multilingual RAG."
    )
    parser.add_argument(
        "--passages",
        type=int,
        default=15000,
        help="Target total source passages to sample (default: 15000)",
    )
    parser.add_argument(
        "--fixed-size",
        type=int,
        default=1000,
        help="Character size for fixed-size chunking (default: 1000)",
    )
    parser.add_argument(
        "--overlap",
        type=int,
        default=150,
        help="Character overlap for fixed-size chunking (default: 150)",
    )
    parser.add_argument(
        "--semantic-size",
        type=int,
        default=1200,
        help="Max character size for sentence-aware semantic chunking (default: 1200)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/processed",
        help="Directory to save processed JSONL files and stats (default: data/processed)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducible sampling (default: 42)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    try:
        run_pipeline(
            target_passages=args.passages,
            fixed_size=args.fixed_size,
            overlap=args.overlap,
            semantic_size=args.semantic_size,
            output_dir=args.output_dir,
            seed=args.seed,
        )
    except KeyboardInterrupt:
        logger.info("Process interrupted by user. Exiting cleanly.")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}", exc_info=True)
        sys.exit(1)
