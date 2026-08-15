# HH Goa 2026 Multilingual Voice-Enabled RAG System
## Data Processing & Chunking Pipeline

This repository contains the data extraction, streaming, and chunking pipeline for the HH Goa 2026 multilingual voice-enabled RAG project.

### Dataset Overview
* **Dataset**: `ai4bharat/MSMARCO-XI`
* **Configuration**: `hi` (Hindi + English)
* **Split**: `train`
* **Target Passages**: 15,000 balanced passages (~7,500 English + ~7,500 Hindi)
* **Streaming**: Zero full-dataset disk caching. Parquet streaming with SSL support and memory-mapped slice reads.

---

### Project Structure
```
.
├── data/
│   ├── raw/
│   └── processed/
│       ├── source_passages.jsonl
│       ├── chunks_fixed.jsonl
│       ├── chunks_semantic.jsonl
│       └── processing_stats.json
├── src/
│   ├── __init__.py
│   └── data/
│       ├── __init__.py
│       └── download_and_process.py
├── tests/
│   ├── __init__.py
│   └── test_chunking.py
├── requirements.txt
├── .gitignore
└── README.md
```

---

### Setup & Installation
```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

### Running the Pipeline

#### 1. Smoke Test (100 Passages)
```bash
python src/data/download_and_process.py --passages 100
```

#### 2. Full 15,000 Source Passages
```bash
python src/data/download_and_process.py --passages 15000
```

#### 3. Custom Chunking Parameters
```bash
python src/data/download_and_process.py \
  --passages 15000 \
  --fixed-size 1000 \
  --overlap 150 \
  --semantic-size 1200 \
  --output-dir data/processed
```

---

### Chunking Strategies
1. **Fixed-Size Chunking (`fixed`)**:
   - Sliding character window of length `1000` with `150` characters overlap.
   - Preserves Unicode (Hindi/English), avoids empty chunks, assigns deterministic unique chunk IDs.

2. **Sentence-Aware Semantic Chunking (`semantic`)**:
   - Multilingual punctuation boundary detection (`.`, `!`, `?`, `।` (Devanagari danda), `\n`).
   - Accumulates full sentences up to `1200` characters.
   - Safe fallback for sentences exceeding chunk limits.

---

### Output Artifacts in `data/processed/`
* `source_passages.jsonl`: Normalized English & Hindi source passages with query & metadata.
* `chunks_fixed.jsonl`: Chunks generated with the fixed-size strategy.
* `chunks_semantic.jsonl`: Chunks generated with the sentence-aware semantic strategy.
* `processing_stats.json`: Detailed execution summary, timing, passage counts, and storage metrics.
