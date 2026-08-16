#!/usr/bin/env python3
"""
Stage 5D: Output & Grounding Guardrail Design Experiment.
Project: HH Goa 2026 Voice-Enabled Multilingual RAG System.

Evaluates 4 lightweight, non-LLM grounding verification strategies:
- Strategy A: Lexical & Entity Overlap
- Strategy B: Answer-to-Context Embedding Similarity
- Strategy C: Sentence-Level Semantic Similarity
- Strategy D: Combined Lexical + Semantic Check

Measures: Accuracy, FP, FN, Latency (P50, P70, P100), and English/Hindi reliability.
"""

import logging
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
from src.retrieval.retriever import get_model

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("grounding_exp")

# Common multilingual stopwords
STOPWORDS_EN: Set[str] = {
    "a", "an", "the", "in", "on", "at", "by", "for", "with", "about", "against",
    "between", "into", "through", "during", "before", "after", "above", "below",
    "to", "from", "up", "down", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "and", "but", "or", "because", "as",
    "until", "while", "of", "it", "its", "this", "that", "these", "those", "i", "we",
    "you", "he", "she", "they", "me", "him", "her", "them", "my", "your", "his", "their",
}

STOPWORDS_HI: Set[str] = {
    "का", "के", "की", "को", "में", "से", "पर", "ने", "और", "या", "है", "हैं",
    "था", "थी", "थे", "होता", "होती", "होते", "किया", "गया", "गई", "गए", "एक",
    "यह", "वह", "इस", "उस", "इन", "उन", "जो", "तो", "भी", "ही", "लिए", "द्वारा",
}


# ==============================================================================
# EVALUATION DATASET (Ground truth: GROUNDED vs NOT_GROUNDED)
# ==============================================================================
TEST_CASES = [
    # 1. Clearly grounded answer (EN)
    {
        "id": "EN-01",
        "type": "Clearly grounded",
        "lang": "EN",
        "context": "Paris is the capital and most populous city of France, situated on the Seine River.",
        "answer": "Paris is the capital of France.",
        "grounded": True,
    },
    # 2. Clearly hallucinated answer (extra ungrounded claim) (EN)
    {
        "id": "EN-02",
        "type": "Clearly hallucinated",
        "lang": "EN",
        "context": "Paris is the capital and most populous city of France, situated on the Seine River.",
        "answer": "Paris is the capital of France and was founded by Alexander the Great in 300 BC.",
        "grounded": False,
    },
    # 3. Paraphrased grounded answer (EN)
    {
        "id": "EN-03",
        "type": "Paraphrased grounded",
        "lang": "EN",
        "context": "Water freezes at 0 degrees Celsius under standard atmospheric pressure conditions.",
        "answer": "At normal atmospheric pressure, water freezes at 0°C.",
        "grounded": True,
    },
    # 4. Partially grounded / ungrounded claim (EN)
    {
        "id": "EN-04",
        "type": "Partially grounded",
        "lang": "EN",
        "context": "Python was created by Guido van Rossum and first released in 1991.",
        "answer": "Python was created by Guido van Rossum in 1991 and became the official language of NASA in 1995.",
        "grounded": False,
    },
    # 5. Completely unrelated answer (EN)
    {
        "id": "EN-05",
        "type": "Completely unrelated",
        "lang": "EN",
        "context": "Paris is the capital and most populous city of France.",
        "answer": "The Pacific Ocean is the largest ocean on Earth.",
        "grounded": False,
    },
    # 6. Short factual answer (EN)
    {
        "id": "EN-06",
        "type": "Short factual",
        "lang": "EN",
        "context": "The Manhattan Project was led by the United States with the support of the United Kingdom and Canada.",
        "answer": "The Manhattan Project was led by the United States.",
        "grounded": True,
    },
    # 7. Ungrounded numbers / statistics (EN)
    {
        "id": "EN-07",
        "type": "Hallucinated numbers",
        "lang": "EN",
        "context": "The project employed thousands of scientists across multiple laboratories.",
        "answer": "The project employed exactly 130,000 scientists and cost $20 billion.",
        "grounded": False,
    },
    # 8. Longer multi-sentence grounded answer (EN)
    {
        "id": "EN-08",
        "type": "Multi-sentence grounded",
        "lang": "EN",
        "context": "Alan Turing was an English mathematician and computer scientist. He developed the concept of the Turing machine in 1936.",
        "answer": "Alan Turing was an English mathematician. In 1936, he introduced the concept of the Turing machine.",
        "grounded": True,
    },
    # 9. Hindi clearly grounded
    {
        "id": "HI-01",
        "type": "Clearly grounded",
        "lang": "HI",
        "context": "मैनहट्टन परियोजना द्वितीय विश्व युद्ध के दौरान पहला परमाणु हथियार विकसित करने का एक गुप्त अनुसंधान था।",
        "answer": "मैनहट्टन परियोजना द्वितीय विश्व युद्ध के दौरान परमाणु हथियार विकसित करने का अनुसंधान था।",
        "grounded": True,
    },
    # 10. Hindi clearly hallucinated
    {
        "id": "HI-02",
        "type": "Clearly hallucinated",
        "lang": "HI",
        "context": "मैनहट्टन परियोजना द्वितीय विश्व युद्ध के दौरान पहला परमाणु हथियार विकसित करने का एक गुप्त अनुसंधान था।",
        "answer": "मैनहट्टन परियोजना का नेतृत्व अल्बर्ट आइंस्टीन ने टोक्यो में किया था।",
        "grounded": False,
    },
    # 11. Hindi paraphrased grounded
    {
        "id": "HI-03",
        "type": "Paraphrased grounded",
        "lang": "HI",
        "context": "एलन ट्यूरिंग ने 1936 में ट्यूरिंग मशीन का आविष्कार किया जिसे आधुनिक कंप्यूटर का आधार माना जाता है।",
        "answer": "आधुनिक कंप्यूटर का आधार मानी जाने वाली ट्यूरिंग मशीन का आविष्कार 1936 में एलन ट्यूरिंग ने किया।",
        "grounded": True,
    },
    # 12. Hindi completely unrelated
    {
        "id": "HI-04",
        "type": "Completely unrelated",
        "lang": "HI",
        "context": "प्रकाश संश्लेषण सूर्य के प्रकाश को रासायनिक ऊर्जा में परिवर्तित करता है।",
        "answer": "भारत की राजधानी नई दिल्ली है और यहाँ लाल किला स्थित है।",
        "grounded": False,
    },
]


def extract_content_tokens(text: str, lang: str) -> List[str]:
    """Tokenizes and filters out punctuation and stopwords."""
    words = re.findall(r"[\w°]+", text.lower())
    stopwords = STOPWORDS_EN if lang == "EN" else STOPWORDS_HI
    return [w for w in words if w not in stopwords and len(w) > 1]


def extract_numbers(text: str) -> Set[str]:
    """Extracts numerical digits, dates, and measurements."""
    return set(re.findall(r"\b\d+[\w°%]*\b", text))


# ==============================================================================
# STRATEGY IMPLEMENTATIONS
# ==============================================================================

def evaluate_strategy_a_lexical(context: str, answer: str, lang: str) -> Tuple[bool, float]:
    """
    Strategy A: Lexical & Entity Overlap with strict numerical verification.
    """
    t0 = time.perf_counter()
    ans_tokens = extract_content_tokens(answer, lang)
    ctx_tokens = set(extract_content_tokens(context, lang))

    if not ans_tokens:
        t1 = time.perf_counter()
        return True, (t1 - t0) * 1000.0

    # 1. Token Recall in context
    matches = sum(1 for t in ans_tokens if t in ctx_tokens)
    recall = matches / len(ans_tokens)

    # 2. Number & entity integrity check
    ans_numbers = extract_numbers(answer)
    ctx_numbers = extract_numbers(context)
    hallucinated_numbers = ans_numbers - ctx_numbers

    # Decision rule: high content token recall AND no hallucinated numbers
    is_grounded = (recall >= 0.65) and (len(hallucinated_numbers) == 0)
    t1 = time.perf_counter()
    return is_grounded, (t1 - t0) * 1000.0


def evaluate_strategy_b_embedding(context: str, answer: str, model: Any) -> Tuple[bool, float]:
    """
    Strategy B: Answer-to-Context Embedding Cosine Similarity.
    """
    t0 = time.perf_counter()
    embs = model.encode([answer, context], normalize_embeddings=True, convert_to_numpy=True)
    cos_sim = float(np.dot(embs[0], embs[1]))
    is_grounded = cos_sim >= 0.70
    t1 = time.perf_counter()
    return is_grounded, (t1 - t0) * 1000.0


def evaluate_strategy_c_sentence(context: str, answer: str, model: Any) -> Tuple[bool, float]:
    """
    Strategy C: Sentence-Level Semantic Similarity.
    """
    t0 = time.perf_counter()
    # Split into sentences (handling . and ।)
    sentences = [s.strip() for s in re.split(r"[.!।?]+", answer) if s.strip()]
    if not sentences:
        t1 = time.perf_counter()
        return True, (t1 - t0) * 1000.0

    ans_embs = model.encode(sentences, normalize_embeddings=True, convert_to_numpy=True)
    ctx_emb = model.encode([context], normalize_embeddings=True, convert_to_numpy=True)[0]

    # Every sentence must have high semantic alignment to the context
    sims = [float(np.dot(s_emb, ctx_emb)) for s_emb in ans_embs]
    min_sim = min(sims)
    is_grounded = min_sim >= 0.65
    t1 = time.perf_counter()
    return is_grounded, (t1 - t0) * 1000.0


def evaluate_strategy_d_combined(context: str, answer: str, lang: str, model: Any) -> Tuple[bool, float]:
    """
    Strategy D: Combined Lexical + Semantic Check.
    """
    t0 = time.perf_counter()
    # 1. Lexical content recall & numbers
    ans_tokens = extract_content_tokens(answer, lang)
    ctx_tokens = set(extract_content_tokens(context, lang))
    recall = sum(1 for t in ans_tokens if t in ctx_tokens) / max(len(ans_tokens), 1)

    ans_numbers = extract_numbers(answer)
    ctx_numbers = extract_numbers(context)
    has_hallucinated_numbers = len(ans_numbers - ctx_numbers) > 0

    # 2. Semantic similarity
    embs = model.encode([answer, context], normalize_embeddings=True, convert_to_numpy=True)
    cos_sim = float(np.dot(embs[0], embs[1]))

    # Combined decision: high semantic similarity AND moderate lexical support AND no hallucinated numbers
    is_grounded = (cos_sim >= 0.68) and (recall >= 0.50) and (not has_hallucinated_numbers)
    t1 = time.perf_counter()
    return is_grounded, (t1 - t0) * 1000.0


# ==============================================================================
# MAIN BENCHMARK RUNNER
# ==============================================================================

def main():
    print("=" * 85)
    print("STAGE 5D: OUTPUT & GROUNDING GUARDRAIL DESIGN EXPERIMENT")
    print("=" * 85)

    model = get_model()

    # Warmup
    evaluate_strategy_b_embedding("warmup context", "warmup answer", model)
    evaluate_strategy_c_sentence("warmup context", "warmup answer", model)

    results: Dict[str, Dict[str, Any]] = {
        "Strategy A (Lexical)": {"decisions": [], "latencies": [], "tp": 0, "tn": 0, "fp": 0, "fn": 0, "en_correct": 0, "hi_correct": 0, "failures": []},
        "Strategy B (Full Embedding)": {"decisions": [], "latencies": [], "tp": 0, "tn": 0, "fp": 0, "fn": 0, "en_correct": 0, "hi_correct": 0, "failures": []},
        "Strategy C (Sentence Semantic)": {"decisions": [], "latencies": [], "tp": 0, "tn": 0, "fp": 0, "fn": 0, "en_correct": 0, "hi_correct": 0, "failures": []},
        "Strategy D (Combined)": {"decisions": [], "latencies": [], "tp": 0, "tn": 0, "fp": 0, "fn": 0, "en_correct": 0, "hi_correct": 0, "failures": []},
    }

    print("\n--- Running Evaluation on 12 Controlled Test Cases ---")
    for case in TEST_CASES:
        cid = case["id"]
        ctx = case["context"]
        ans = case["answer"]
        lang = case["lang"]
        gt = case["grounded"]

        # Strategy A
        a_pred, a_lat = evaluate_strategy_a_lexical(ctx, ans, lang)
        # Strategy B
        b_pred, b_lat = evaluate_strategy_b_embedding(ctx, ans, model)
        # Strategy C
        c_pred, c_lat = evaluate_strategy_c_sentence(ctx, ans, model)
        # Strategy D
        d_pred, d_lat = evaluate_strategy_d_combined(ctx, ans, lang, model)

        for name, pred, lat in [
            ("Strategy A (Lexical)", a_pred, a_lat),
            ("Strategy B (Full Embedding)", b_pred, b_lat),
            ("Strategy C (Sentence Semantic)", c_pred, c_lat),
            ("Strategy D (Combined)", d_pred, d_lat),
        ]:
            r = results[name]
            r["decisions"].append(pred)
            r["latencies"].append(lat)
            is_correct = (pred == gt)

            if gt and pred:
                r["tp"] += 1
            elif not gt and not pred:
                r["tn"] += 1
            elif not gt and pred:
                r["fp"] += 1  # Missed hallucination
                r["failures"].append((cid, case["type"], "False Positive (Missed Hallucination)"))
            elif gt and not pred:
                r["fn"] += 1  # False rejection of grounded answer
                r["failures"].append((cid, case["type"], "False Negative (Wrongly Rejected Grounded)"))

            if is_correct:
                if lang == "EN":
                    r["en_correct"] += 1
                else:
                    r["hi_correct"] += 1

        print(f"[{cid} {lang}] GT: {'GROUND' if gt else 'UNGRND'} | A:{'✓' if a_pred==gt else '✗'} | B:{'✓' if b_pred==gt else '✗'} | C:{'✓' if c_pred==gt else '✗'} | D:{'✓' if d_pred==gt else '✗'} | {case['type']}")

    total_cases = len(TEST_CASES)
    total_en = sum(1 for c in TEST_CASES if c["lang"] == "EN")
    total_hi = sum(1 for c in TEST_CASES if c["lang"] == "HI")

    print("\n" + "=" * 85)
    print("STRATEGY COMPARISON REPORT")
    print("=" * 85)
    print(f"{'Strategy':<30} {'Accuracy':<10} {'EN Acc':<10} {'HI Acc':<10} {'P50 (ms)':<10} {'P70 (ms)':<10} {'P100 (ms)':<10}")
    print("-" * 92)

    for name, r in results.items():
        acc = (r["tp"] + r["tn"]) / total_cases * 100.0
        en_acc = r["en_correct"] / total_en * 100.0
        hi_acc = r["hi_correct"] / total_hi * 100.0
        p50 = float(np.percentile(r["latencies"], 50))
        p70 = float(np.percentile(r["latencies"], 70))
        p100 = float(np.max(r["latencies"]))

        print(f"{name:<30} {acc:>5.1f}%     {en_acc:>5.1f}%     {hi_acc:>5.1f}%     {p50:>6.2f} ms  {p70:>6.2f} ms  {p100:>6.2f} ms")

    print("\n" + "=" * 85)
    print("DETAILED ERROR ANALYSIS & FAILURE CASES")
    print("=" * 85)
    for name, r in results.items():
        print(f"\n--- {name} ---")
        print(f"  True Positives:  {r['tp']} / 5")
        print(f"  True Negatives:  {r['tn']} / 7")
        print(f"  False Positives: {r['fp']} (Missed Hallucinations)")
        print(f"  False Negatives: {r['fn']} (Rejected Valid Grounded)")
        if r["failures"]:
            for fid, ftype, fmsg in r["failures"]:
                print(f"    - [{fid}] {ftype}: {fmsg}")
        else:
            print("    - None (100% Accuracy on evaluation dataset)")


if __name__ == "__main__":
    main()
