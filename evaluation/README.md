# HH_RAG Evaluation & Latency Benchmarking

Reproducible latency benchmarking for the HH Goa 2026 Task 2 requirement of
**P50 / P70 / P100 latency measured across a set of queries** — not a single
best-case request.

```
evaluation/
├── queries.json      50 benchmark inputs (English + Hindi, short + long, answer + refuse)
├── benchmark.py      runner: sends every query to POST /api/query and records latency
├── metrics.py        deterministic percentile + success-rate calculations
├── results/          timestamped raw runs (git-ignored)
└── README.md
```

---

## What is measured

There are three distinct latencies. Keeping them separate is the whole point.

| Metric | Measured by | Meaning |
| --- | --- | --- |
| **`client_total_ms`** | this script, `time.perf_counter()` | HTTP round trip: from just before the request is sent until the response body has been read. Includes transport, framework and service time. **This is the user-facing number.** |
| **`server_total_ms`** | the API route, `src/utils/timing.Timer` | Backend wall clock for the RAG service call alone. A subset of client latency. Never a sum of stages. |
| **stage fields** | each pipeline stage | Duration of one operation (`stt_ms`, `embedding_ms`, `retrieval_ms`, `generation_ms`, `guardrail_ms`). `0` means the stage did not run or is not yet instrumented — never "instant". |

So `sum(stages) <= server_total_ms <= client_total_ms`. The gaps are real and
diagnostic: stages vs server total is un-instrumented backend work, server total
vs client total is framework plus transport overhead.

The response header `X-Process-Time-Ms` carries full server request duration
(routing + validation + service + serialisation) and is recorded per query as
`server_process_ms`.

Latency values are taken verbatim from real clocks. The benchmark never
manufactures, scales, or smooths a measurement.

---

## Percentiles

Percentiles use the **nearest-rank** method — no interpolation:

```
rank  = ceil(p / 100 * n)      clamped to [1, n]
value = sorted(values)[rank - 1]
```

* Every reported number is a measurement that actually occurred.
* **P100 is always the maximum observed value.**
* Re-running the same samples always produces the same percentiles.
* Example: for `[10, 20, 30, 40]` → P50 = 20 (rank 2), P70 = 30 (rank 3), P100 = 40.
  Note this differs from an interpolated median of 25; that is intentional.

Only successful requests contribute samples. If every request fails, the
percentiles are reported as `null` / `n/a` rather than `0`, so an outage can
never be mistaken for a fast run.

Also reported: `successful_requests`, `failed_requests`, `success_rate`.

---

## Latency target

The benchmark compares **client-side P100** against the 200 ms target, because
that is the end-to-end time a user actually waits:

```
Latency target: <200ms (measured against client round trip)
Client P100: 184.00ms
Status: PASS
```

`PASS` is emitted only when the measured value is strictly below 200 ms.
Otherwise the status is `ABOVE TARGET`, or `NOT MEASURED` when no successful
request produced a latency value.

When no pipeline stage reports measurable work, the report appends an explicit
note that the run exercised HTTP overhead only. A `PASS` produced against the
mock service is **not** evidence about the integrated system.

---

## Running the benchmark

Start the API first, then:

```bash
python evaluation/benchmark.py --limit 50
```

Options:

| Flag | Default | Purpose |
| --- | --- | --- |
| `--url` | `http://localhost:8000` | API base URL |
| `--input` | `evaluation/queries.json` | Query set |
| `--output` | timestamped file in `results/` | Result file path |
| `--limit` | all | Max number of queries to run |
| `--delay` | `0.05` | Seconds between requests, to avoid overwhelming a local server |
| `--timeout` | `30` | Per-request timeout in seconds |

```bash
python evaluation/benchmark.py \
  --url http://localhost:8000 \
  --input evaluation/queries.json \
  --limit 50
```

Per-query progress is written to stderr; the summary report goes to stdout.
Exit code is `0` when every request succeeded, `1` otherwise.

Each result record stores the `X-Request-ID` returned by the API, so a slow
benchmark query can be traced directly to its backend log line.

A failed request is recorded with `success: false` and an error string, and the
run continues with the next query — one dead request never aborts a benchmark.

---

## Results

Each run writes a new timestamped file and never overwrites an existing one:

```
evaluation/results/benchmark_2026-08-16T010000.json
```

Structure:

```json
{
  "metadata": { "timestamp": "...", "base_url": "...", "endpoint": "/api/query",
                "input_file": "...", "query_count": 50 },
  "summary":  { "client_total_ms": { "count": 50, "p50": ..., "p70": ..., "p100": ... },
                "server_total_ms": { ... }, "retrieval_ms": { ... },
                "generation_ms": { ... }, "guardrail_ms": { ... },
                "requests": { ... }, "latency_target": { ... } },
  "queries":  [ { "query_id": "q001", "client_total_ms": ..., "server_total_ms": ...,
                  "grounded": true, "confidence": 0.93, "error": null }, ... ]
}
```

`results/` is git-ignored. Benchmark output is evidence of a specific run on
specific hardware and should be attached to a submission deliberately, not
committed by accident.

---

## Query set

`queries.json` holds 50 benchmark inputs covering English and Hindi factual
questions, short keyword queries, long multi-clause questions, Devanagari
punctuation (`।`, `?`), and queries that a correct system should refuse
(unanswerable, out-of-corpus, private data, prompt injection).

```json
{ "id": "q001", "query": "...", "language": "en", "expected_behavior": "answer" }
```

`expected_behavior` is `answer` or `refuse`. These are **benchmark inputs only** —
no expected answers are asserted yet. Once retrieval is integrated, this set will
be replaced/expanded with queries derived from MSMARCO-XI passages with known
relevant chunks, which will enable grounding and accuracy evaluation on top of
latency.

---

## Important: current numbers are not submission numbers

The API is presently backed by `src/services/mock_rag.py`, which performs **no**
STT, embedding, retrieval, generation or guardrail work and therefore reports
`0` for every stage. Its `total_ms` is a genuine measurement — of a function that
returns canned text. Therefore:

* Current server-side numbers describe dictionary lookups, not a RAG pipeline.
* Current client-side numbers describe HTTP and framework overhead only.
* **No latency claim may be made from a mock run, passing or failing.**

Benchmark results submitted for HH Goa 2026 must be regenerated against the
actual deployed pipeline once embeddings + Qdrant retrieval (Person 1) and
Sarvam STT + LLM generation + guardrails (Person 2) are integrated. The runner,
metrics, and output format stay unchanged, because they depend only on the
existing API response contract.

---

## Voice benchmarking

Text and voice are treated as **separate pipelines** and their results are never
merged, because voice additionally carries STT latency. `build_report()` takes a
`pipeline` argument (`PIPELINE_TEXT` / `PIPELINE_VOICE`), records it in the report
metadata alongside the endpoint, and the rendered report is headed `TEXT PIPELINE`
or `VOICE PIPELINE`.

The voice runner itself is not implemented yet: `post_json` is endpoint-agnostic,
so adding it means supplying a fixed set of audio files and a multipart body
builder, reusing the same metrics and report format. It is deliberately deferred
until real STT exists — benchmarking a mock transcript would measure nothing.

---

## Tests

```bash
pytest tests/test_metrics.py tests/test_benchmark.py -q
```

Covers percentile behaviour (P50/P70/P100, single value, unsorted input, empty
input), success-rate accounting, latency-target strictness, and that a failed API
request does not terminate a benchmark run.
