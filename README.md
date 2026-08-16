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

---

## Runtime API (Mock Layer)

FastAPI service exposing the stable contract the frontend and downstream teams build against.
The retrieval/STT/LLM pipeline is currently mocked by `src/services/mock_rag.py` and will be
replaced without changing the API contract.

### Run locally
```bash
uvicorn src.api.main:app --reload
```
Interactive docs: http://127.0.0.1:8000/docs

### Endpoints
| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/api/health` | Liveness check |
| `POST` | `/api/query` | Text query -> `RagResponse` |
| `POST` | `/api/voice` | Multipart audio upload (`file`) -> `RagResponse` with mock transcript |

CORS is enabled for `http://localhost:5173` and `http://127.0.0.1:5173`
(override with `HH_RAG_CORS_ORIGINS`).

### Integration contract

The API depends on the `RAGService` abstraction in
[src/services/rag_service.py](src/services/rag_service.py), not on any concrete
implementation:

```
API route -> Depends(get_rag_service) -> RAGService
                                          ├─ MockRAGService   (today)
                                          └─ RealRAGService   (retriever + generator + guardrails)
```

To plug in the real pipeline, implement `RAGService.query()` / `RAGService.voice()`
and return it from `get_rag_service()`. Nothing else changes.

**Errors** always use one envelope, never a stack trace:

```json
{ "error": { "code": "RETRIEVAL_FAILED", "message": "Unable to retrieve relevant context." } }
```

Codes: `INVALID_QUERY`, `AUDIO_INVALID`, `STT_FAILED`, `RETRIEVAL_FAILED`,
`GENERATION_FAILED`, `GUARDRAIL_FAILED`, `NOT_FOUND`, `INTERNAL_ERROR`. Raise the
matching exception from `rag_service.py`; the HTTP status is derived from it.

**Correlation**: every response carries `X-Request-ID` (echoed from the request
when supplied, otherwise generated) and the same ID appears in the server log line
and in benchmark result records.

**Languages**: `en` and `hi` today. The set lives only in
[src/config.py](src/config.py) — adding `bn`/`ta`/`te`/`mr` is one enum member.

**Sources**: `strategy` is optional and may be `null`; the frontend renders
"unavailable" rather than inventing a value.

### Configuration
Copy [.env.example](.env.example) to `.env` (backend) and
[web/.env.example](web/.env.example) to `web/.env` (frontend). No real secrets are
committed.

### API tests
```bash
pytest tests/test_api.py tests/test_rag_service.py -q
```

---

## Frontend (`web/`)

React + Vite + TypeScript + Tailwind CSS client. All backend calls go through
`web/src/api/rag.ts`, so the mock service can be replaced without touching components.

```bash
cd web
npm install
npm run dev        # http://localhost:5173
```

The backend must be running on `http://localhost:8000`. Override with
`VITE_API_BASE_URL` in `web/.env` (see `web/.env.example`).

Microphone capture uses the browser `MediaRecorder` API and requires a secure
context — `localhost` qualifies.

---

## Evaluation & Benchmarking (`evaluation/`)

Reproducible P50/P70/P100 latency benchmark over a 50-query bilingual set. With
the API running:

```bash
python evaluation/benchmark.py --limit 50
```

Results are written to `evaluation/results/` (git-ignored). See
[evaluation/README.md](evaluation/README.md) for methodology, the client vs
server latency distinction, and why benchmark numbers must be regenerated
against the real pipeline before submission.


