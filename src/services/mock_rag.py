"""Deterministic mock RAG service.

Provides realistic, stable responses so the frontend and API layer can be built
before the real retrieval (Person 1) and STT/LLM/guardrail (Person 2) pipelines
exist. :class:`MockRAGService` implements :class:`~src.services.rag_service.RAGService`
and is the only thing a real implementation has to replace.

The answers are canned; the **latency is not**. This service performs no STT,
embedding, retrieval, generation or guardrail work, so it reports 0 ms for every
stage. The only latency it contributes is its real execution time, which the API
layer measures and reports as ``total_ms``.
"""

import re
from typing import Dict, List, Optional

from src.api.schemas.rag import LatencyMetrics, RagResponse, Source
from src.config import DEFAULT_LANGUAGE, Language
from src.services.rag_service import (
    AudioInput,
    InvalidQueryError,
    RAGService,
)

_DEVANAGARI_RE = re.compile(r"[\u0900-\u097F]")

MOCK_TRANSCRIPT = "प्रकाश संश्लेषण क्या है?"

_FALLBACK_ANSWER = {
    "en": (
        "I could not find a grounded answer for this question in the indexed "
        "passages. Please rephrase or ask about a topic covered by the corpus."
    ),
    "hi": (
        "इस प्रश्न का उत्तर अनुक्रमित अनुच्छेदों में नहीं मिला। कृपया प्रश्न को दोबारा "
        "लिखें या कॉर्पस में मौजूद किसी विषय के बारे में पूछें।"
    ),
}

# Keyword -> canned knowledge entry. Keys are matched case-insensitively.
_TOPICS: List[Dict] = [
    {
        "id": "photosynthesis",
        "keywords": [
            "photosynthesis",
            "chlorophyll",
            "प्रकाश संश्लेषण",
            "प्रकाशसंश्लेषण",
            "पर्णहरित",
            "क्लोरोफिल",
        ],
        "answer": {
            "en": (
                "Photosynthesis is the process by which green plants, algae and "
                "some bacteria convert light energy into chemical energy. "
                "Chlorophyll in the chloroplasts absorbs sunlight, and carbon "
                "dioxide and water are converted into glucose and oxygen."
            ),
            "hi": (
                "प्रकाश संश्लेषण वह प्रक्रिया है जिसके द्वारा हरे पौधे, शैवाल और कुछ "
                "जीवाणु प्रकाश ऊर्जा को रासायनिक ऊर्जा में बदलते हैं। हरितलवक में "
                "उपस्थित क्लोरोफिल सूर्य के प्रकाश को अवशोषित करता है और कार्बन "
                "डाइऑक्साइड तथा जल से ग्लूकोज और ऑक्सीजन बनते हैं।"
            ),
        },
        "confidence": 0.93,
        "sources": [
            {
                "chunk_id": "msmarco-xi::doc_10421::chunk_0",
                "doc_id": "doc_10421",
                "text": (
                    "Photosynthesis converts light energy into chemical energy "
                    "stored in glucose, releasing oxygen as a by-product."
                ),
                "language": "en",
                "score": 0.91,
                "strategy": "semantic",
            },
            {
                "chunk_id": "msmarco-xi::doc_10421::chunk_1",
                "doc_id": "doc_10421",
                "text": (
                    "पौधों की पत्तियों में उपस्थित क्लोरोफिल सूर्य के प्रकाश को "
                    "अवशोषित करके प्रकाश संश्लेषण की क्रिया संपन्न करता है।"
                ),
                "language": "hi",
                "score": 0.87,
            },
        ],
    },
    {
        "id": "goa",
        "keywords": ["goa", "गोवा", "beach", "समुद्र तट"],
        "answer": {
            "en": (
                "Goa is a state on the western coast of India, known for its "
                "beaches, Portuguese-era architecture and tourism-led economy."
            ),
            "hi": (
                "गोवा भारत के पश्चिमी तट पर स्थित एक राज्य है, जो अपने समुद्र तटों, "
                "पुर्तगाली काल की वास्तुकला और पर्यटन आधारित अर्थव्यवस्था के लिए "
                "प्रसिद्ध है।"
            ),
        },
        "confidence": 0.88,
        "sources": [
            {
                "chunk_id": "msmarco-xi::doc_20877::chunk_0",
                "doc_id": "doc_20877",
                "text": (
                    "Goa is India's smallest state by area and is located on the "
                    "Konkan coast along the Arabian Sea."
                ),
                "language": "en",
                "score": 0.84,
                "strategy": "fixed",
            }
        ],
    },
    {
        "id": "water_cycle",
        "keywords": [
            "water cycle",
            "evaporation",
            "जल चक्र",
            "वाष्पीकरण",
        ],
        "answer": {
            "en": (
                "The water cycle describes the continuous movement of water "
                "through evaporation, condensation, precipitation and collection."
            ),
            "hi": (
                "जल चक्र पृथ्वी पर जल की निरंतर गति का वर्णन करता है, जिसमें "
                "वाष्पीकरण, संघनन, वर्षण और संग्रहण शामिल हैं।"
            ),
        },
        "confidence": 0.9,
        "sources": [
            {
                "chunk_id": "msmarco-xi::doc_33150::chunk_2",
                "doc_id": "doc_33150",
                "text": (
                    "Evaporation, condensation and precipitation move water "
                    "between the oceans, atmosphere and land."
                ),
                "language": "en",
                "score": 0.86,
            }
        ],
    },
]


def detect_language(text: str) -> Language:
    """Return Hindi when the text contains Devanagari characters, else the default.

    Script detection is intentionally isolated here; a real language identifier
    can replace it without touching the rest of the application.
    """
    return Language.HI if _DEVANAGARI_RE.search(text) else DEFAULT_LANGUAGE


def _match_topic(query: str) -> Optional[Dict]:
    lowered = query.lower()
    for topic in _TOPICS:
        if any(keyword.lower() in lowered for keyword in topic["keywords"]):
            return topic
    return None


def _mock_latency() -> LatencyMetrics:
    """All zeros: no stage below is really executed, so nothing may be claimed.

    A real implementation replaces this by timing each stage with
    :class:`src.utils.timing.Timer`. ``total_ms`` is filled in by the API layer
    from the measured wall-clock duration of the service call.
    """
    return LatencyMetrics()


def answer_query(
    query: str,
    transcript: Optional[str] = None,
) -> RagResponse:
    """Return a deterministic mock RAG response for the given query."""
    query = query.strip()
    language = detect_language(query)
    topic = _match_topic(query)

    if topic is None:
        return RagResponse(
            transcript=transcript,
            query=query,
            language=language,
            answer=_FALLBACK_ANSWER[language.value],
            grounded=False,
            confidence=0.21,
            sources=[],
            latency=_mock_latency(),
        )

    return RagResponse(
        transcript=transcript,
        query=query,
        language=language,
        answer=topic["answer"][language.value],
        grounded=True,
        confidence=topic["confidence"],
        sources=[Source(**source) for source in topic["sources"]],
        latency=_mock_latency(),
    )


def transcribe_audio(filename: str, audio_bytes: bytes) -> str:
    """Mock STT: returns a fixed transcript without inspecting the audio.

    Replaced later by the Sarvam STT integration; the signature is the seam.
    Since no transcription happens, the caller reports ``stt_ms`` as 0.
    """
    return MOCK_TRANSCRIPT


class MockRAGService(RAGService):
    """Deterministic stand-in for the real retrieval + generation pipeline."""

    def query(self, query: str) -> RagResponse:
        if not query or not query.strip():
            raise InvalidQueryError("Query must not be empty.")
        return answer_query(query)

    def voice(self, audio: AudioInput) -> RagResponse:
        transcript = transcribe_audio(audio.filename, audio.data)
        return answer_query(transcript, transcript=transcript)
