"""
Input and Context Guardrails for Multilingual RAG Orchestration.
Project: HH Goa 2026 Voice-Enabled Multilingual RAG System.

Provides deterministic, lightweight, sub-millisecond guardrails:
1. Input Validation (empty/whitespace/malformed queries)
2. Safety Guardrail (deterministic refusal for dangerous/harmful content)
3. Context Sufficiency Guardrail (similarity score threshold & chunk availability)

Zero additional LLM calls or external network dependencies.
"""

import logging
import re
from typing import Any, List, Optional, Tuple

from src.orchestration.schemas import RetrievedChunk

logger = logging.getLogger("guardrails")

# Minimum cosine/IP similarity threshold on normalized all-MiniLM-L6-v2 embeddings.
# Calibrated against MSMARCO-XI index:
# - Highly relevant: 0.70 - 0.90
# - Marginal/Partial: 0.45 - 0.65
# - Random nonsense/unsupported: < 0.35
DEFAULT_SIMILARITY_THRESHOLD = 0.35

# Deterministic safety patterns for clearly harmful/dangerous queries
# (weapons/explosives synthesis, cyberattacks/malware creation, self-harm)
UNSAFE_PATTERNS = [
    # Weapons & Explosives (English)
    re.compile(r"\b(how to (make|build|create|synthesize)|recipe for)\b.*\b(bomb|explosive|ied|molotov|poison gas|chemical weapon|biological weapon)\b", re.IGNORECASE),
    # Weapons & Explosives (Hindi)
    re.compile(r"(बम|विस्फोटक|हथियार).*(बनाने|निर्माण|विधि|तरीका)", re.IGNORECASE),
    
    # Malware & Cyberattacks (English)
    re.compile(r"\b(how to (write|create|build)|code for)\b.*\b(malware|ransomware|keylogger|ddos attack|trojan virus|exploit payload)\b", re.IGNORECASE),
    # Malware & Cyberattacks (Hindi)
    re.compile(r"(हैक|रैनसमवेयर|मैलवेयर).*(बनाने|लिखने|कोड|तरीका)", re.IGNORECASE),

    # Self-harm (English)
    re.compile(r"\b(how to (commit suicide|kill myself|harm myself))\b", re.IGNORECASE),
    # Self-harm (Hindi)
    re.compile(r"(आत्महत्या|खुद को नुकसान).*(कैसे|तरीका|विधि)", re.IGNORECASE),
]



def validate_input_guardrail(query: Any) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Validates that the input query is a valid, non-empty, non-whitespace string.

    Returns:
        (is_valid, error_reason, message)
    """
    if not isinstance(query, str):
        return False, "invalid_query_type", "Query must be a string."
    cleaned = query.strip()
    if not cleaned:
        return False, "empty_query", "Query cannot be empty or whitespace-only."
    return True, None, None


def safety_guardrail(query: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Evaluates query against deterministic safety rules without external network or LLM calls.

    Returns:
        (is_safe, refusal_reason, refusal_message)
    """
    cleaned = query.strip()
    for pattern in UNSAFE_PATTERNS:
        if pattern.search(cleaned):
            logger.warning(f"Safety guardrail triggered for query: '{cleaned[:40]}...'")
            return (
                False,
                "unsafe_content_refusal",
                "I cannot fulfill this request as it involves potentially dangerous or harmful content.",
            )
    return True, None, None


def context_sufficiency_guardrail(
    chunks: List[RetrievedChunk],
    min_similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Evaluates whether the retrieved chunks provide sufficient relevance to answer the query.

    Returns:
        (is_sufficient, reason, message)
    """
    if not chunks or len(chunks) == 0:
        return False, "no_context_retrieved", "No relevant context was found for this query."

    top_score = max(chunk.score for chunk in chunks)
    if top_score < min_similarity_threshold:
        logger.info(f"Context guardrail: top score {top_score:.4f} is below threshold {min_similarity_threshold:.2f}")
        return (
            False,
            "insufficient_context",
            "The available knowledge context is insufficient to answer this query accurately.",
        )

    return True, None, None
