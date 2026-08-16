"""
Production Output & Grounding Guardrail.
Project: HH Goa 2026 Voice-Enabled Multilingual RAG System.

Implements lightweight, non-LLM, sub-millisecond grounding verification:
- Lexical & named entity overlap against retrieved context
- Strict numerical & date verification
- Common measurement and notation normalization (e.g., 0°C <-> 0 degrees Celsius)
- Stopword-aware token analysis across English and Hindi

Zero additional LLM or network calls.
"""

from dataclasses import dataclass, field
import logging
import re
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger("grounding")

# Common multilingual stopwords
STOPWORDS_EN: Set[str] = {
    "a", "an", "the", "in", "on", "at", "by", "for", "with", "about", "against",
    "between", "into", "through", "during", "before", "after", "above", "below",
    "to", "from", "up", "down", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "and", "but", "or", "because", "as",
    "until", "while", "of", "it", "its", "this", "that", "these", "those", "i", "we",
    "you", "he", "she", "they", "me", "him", "her", "them", "my", "your", "his", "their",
    "also", "which", "who", "whom", "what", "where", "when", "how", "can", "could",
    "will", "would", "shall", "should", "may", "might", "must",
}

STOPWORDS_HI: Set[str] = {
    "का", "के", "की", "को", "में", "से", "पर", "ने", "और", "या", "है", "हैं",
    "था", "थी", "थे", "होता", "होती", "होते", "किया", "गया", "गई", "गए", "एक",
    "यह", "वह", "इस", "उस", "इन", "उन", "जो", "तो", "भी", "ही", "लिए", "द्वारा",
    "सकता", "सकती", "सकते", "होना", "होने", "रहा", "रही", "रहे", "कि", "अपने", "अपनी",
}

# Measurement and symbol normalization mappings
MEASUREMENT_PATTERNS = [
    (re.compile(r"(\d+)\s*(?:°\s*c|degrees?\s+celsius)", re.IGNORECASE), r"\1_deg_c"),
    (re.compile(r"(\d+)\s*(?:°\s*f|degrees?\s+fahrenheit)", re.IGNORECASE), r"\1_deg_f"),
    (re.compile(r"(\d+)\s*%", re.IGNORECASE), r"\1_percent"),
    (re.compile(r"(\d+)\s*percent", re.IGNORECASE), r"\1_percent"),
    (re.compile(r"\$(\d+)", re.IGNORECASE), r"\1_dollars"),
    (re.compile(r"(\d+)\s*dollars?", re.IGNORECASE), r"\1_dollars"),
]


@dataclass
class GroundingResult:
    """
    Structured outcome of grounding validation.
    """
    grounded: bool
    reason: Optional[str] = None
    overlap_score: float = 0.0
    unsupported_claims: List[str] = field(default_factory=list)
    numerical_mismatches: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "grounded": self.grounded,
            "reason": self.reason,
            "overlap_score": round(self.overlap_score, 4),
            "unsupported_claims": self.unsupported_claims,
            "numerical_mismatches": self.numerical_mismatches,
        }


def normalize_text_units(text: str) -> str:
    """Normalizes common physical units and symbols to canonical tokens."""
    normalized = text
    for pattern, repl in MEASUREMENT_PATTERNS:
        normalized = pattern.sub(repl, normalized)
    return normalized


def extract_content_tokens(text: str, lang: Optional[str] = None) -> List[str]:
    """Tokenizes normalized text and filters stopwords and punctuation."""
    norm_text = normalize_text_units(text)
    words = re.findall(r"[\w_]+", norm_text.lower())
    
    # Detect language if not explicitly provided
    is_hindi = (lang == "hi" or lang == "HI") or any(
        '\u0900' <= char <= '\u097F' for char in text
    )
    stopwords = STOPWORDS_HI if is_hindi else STOPWORDS_EN
    
    return [w for w in words if w not in stopwords and len(w) > 1]


def extract_numbers_and_quantities(text: str) -> Set[str]:
    """Extracts numbers, canonical unit tokens, years, and measurements."""
    norm_text = normalize_text_units(text)
    # Match standalone numbers or normalized unit tokens like 0_deg_c, 1991, 100_percent
    tokens = re.findall(r"\b(?:\d+[\w_]*|\w+_\d+|\d+)\b", norm_text)
    numbers = set()
    for t in tokens:
        if any(char.isdigit() for char in t):
            numbers.add(t.lower())
    return numbers


def extract_named_entities(text: str) -> Set[str]:
    """
    Extracts proper named entities (capitalized words not starting a sentence).
    """
    entities = set()
    sentences = re.split(r"[.!?]+", text)
    for s in sentences:
        words = s.strip().split()
        if len(words) > 1:
            # Check words after the first word in each sentence
            for w in words[1:]:
                clean_w = re.sub(r"[^\w]", "", w)
                if clean_w and clean_w[0].isupper() and len(clean_w) > 1 and clean_w.lower() not in STOPWORDS_EN:
                    entities.add(clean_w.lower())
    return entities


def verify_grounding(
    query: str,
    retrieved_chunks: List[Any],
    answer: str,
    language: Optional[str] = None,
    min_overlap_threshold: float = 0.65,
) -> GroundingResult:
    """
    Evaluates whether the generated answer is strictly grounded in the retrieved context.

    Args:
        query: User query string.
        retrieved_chunks: List of retrieved chunk dictionaries or RetrievedChunk objects.
        answer: Generated answer text.
        language: Language tag ('en', 'hi', etc.).
        min_overlap_threshold: Minimum required content token overlap ratio.

    Returns:
        GroundingResult with grounded flag, overlap score, and mismatch details.
    """
    if not answer or not answer.strip():
        return GroundingResult(
            grounded=False,
            reason="empty_answer",
            overlap_score=0.0,
            unsupported_claims=["Empty or whitespace answer."],
        )

    # 1. Combine retrieved context text
    context_blocks = []
    for c in retrieved_chunks:
        if isinstance(c, dict):
            text = c.get("text", "")
        else:
            text = getattr(c, "text", "")
        if text:
            context_blocks.append(text)
    full_context = " ".join(context_blocks)

    if not full_context.strip():
        return GroundingResult(
            grounded=False,
            reason="empty_context",
            overlap_score=0.0,
            unsupported_claims=["No retrieved context provided."],
        )

    # 2. Extract content tokens & entities
    ans_tokens = extract_content_tokens(answer, language)
    ctx_tokens = set(extract_content_tokens(full_context, language))
    # Also include query tokens to allow answering directly about terms in the prompt
    query_tokens = set(extract_content_tokens(query, language))
    supported_vocabulary = ctx_tokens.union(query_tokens)

    if not ans_tokens:
        # Answer consists purely of stopwords or affirmative short phrase
        return GroundingResult(grounded=True, reason="grounded_affirmation", overlap_score=1.0)

    matched_tokens = [t for t in ans_tokens if t in supported_vocabulary]
    overlap_score = len(matched_tokens) / len(ans_tokens)

    # 3. Numerical & Quantitative Consistency Check
    ans_numbers = extract_numbers_and_quantities(answer)
    ctx_numbers = extract_numbers_and_quantities(full_context).union(
        extract_numbers_and_quantities(query)
    )
    unsupported_numbers = ans_numbers - ctx_numbers

    # 4. Named Entity Integrity Check (English)
    ans_entities = extract_named_entities(answer)
    ctx_entities = extract_named_entities(full_context).union(extract_named_entities(query))
    # Also check if entity is in supported vocabulary tokens
    unsupported_entities = {e for e in ans_entities if e not in ctx_entities and e not in supported_vocabulary}

    # 5. Determine Grounding Decision
    unsupported_claims = []
    numerical_mismatches = list(unsupported_numbers)

    if unsupported_numbers:
        unsupported_claims.append(f"Answer introduces unsupported numerical values: {sorted(list(unsupported_numbers))}")

    if unsupported_entities:
        unsupported_claims.append(f"Answer introduces unsupported named entities: {sorted(list(unsupported_entities))}")

    if overlap_score < min_overlap_threshold:
        missing_tokens = [t for t in ans_tokens if t not in supported_vocabulary]
        unsupported_claims.append(f"Low contextual content overlap ({overlap_score:.1%}). Missing terms: {missing_tokens[:5]}")

    is_grounded = (
        (len(unsupported_numbers) == 0)
        and (len(unsupported_entities) == 0)
        and (overlap_score >= min_overlap_threshold)
    )
    
    if is_grounded:
        reason = "grounded"
    elif unsupported_numbers:
        reason = "numerical_mismatch"
    elif unsupported_entities:
        reason = "unsupported_entity"
    else:
        reason = "unsupported_content"

    return GroundingResult(
        grounded=is_grounded,
        reason=reason,
        overlap_score=overlap_score,
        unsupported_claims=unsupported_claims,
        numerical_mismatches=numerical_mismatches,
    )
