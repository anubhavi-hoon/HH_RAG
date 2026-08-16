"""Unit tests for production output grounding and hallucination guardrail."""

import pytest

from src.orchestration.grounding import GroundingResult, verify_grounding
from src.orchestration.schemas import RetrievedChunk


@pytest.fixture
def sample_context():
    return [
        RetrievedChunk(
            chunk_id="c1",
            text="Water freezes at 0 degrees Celsius under standard atmospheric pressure conditions.",
            score=0.88,
        ),
        RetrievedChunk(
            chunk_id="c2",
            text="Alan Turing developed the concept of the Turing machine in 1936 in England.",
            score=0.85,
        ),
    ]


def test_grounding_directly_grounded_answer(sample_context):
    """Test directly supported factual answer passes grounding."""
    res = verify_grounding(
        query="When did Alan Turing develop the Turing machine?",
        retrieved_chunks=sample_context,
        answer="Alan Turing developed the Turing machine in 1936 in England.",
        language="en",
    )
    assert isinstance(res, GroundingResult)
    assert res.grounded is True
    assert res.reason == "grounded"
    assert len(res.numerical_mismatches) == 0


def test_grounding_paraphrased_grounded_answer(sample_context):
    """Test paraphrased answer with measurement normalization passes grounding."""
    res = verify_grounding(
        query="At what temperature does water freeze?",
        retrieved_chunks=sample_context,
        answer="At standard atmospheric pressure, water freezes at 0°C.",
        language="en",
    )
    assert res.grounded is True
    assert res.reason == "grounded"


def test_grounding_unsupported_entity(sample_context):
    """Test answer with an ungrounded entity fails grounding."""
    res = verify_grounding(
        query="Who developed the Turing machine?",
        retrieved_chunks=sample_context,
        answer="Alan Turing and Albert Einstein together developed the Turing machine.",
        language="en",
    )
    # Einstein is not in context
    assert res.grounded is False
    assert "einstein" in str(res.unsupported_claims).lower() or res.overlap_score < 0.85


def test_grounding_fabricated_number(sample_context):
    """Test answer introducing unsupported numbers/quantities fails grounding."""
    res = verify_grounding(
        query="At what temperature does water freeze?",
        retrieved_chunks=sample_context,
        answer="Water freezes at 0 degrees Celsius and boils at 100 degrees Celsius.",
        language="en",
    )
    # 100 is not in context
    assert res.grounded is False
    assert len(res.numerical_mismatches) > 0 or not res.grounded


def test_grounding_unsupported_date_year(sample_context):
    """Test answer with hallucinated date/year fails grounding."""
    res = verify_grounding(
        query="When did Turing invent the machine?",
        retrieved_chunks=sample_context,
        answer="Alan Turing developed the Turing machine in 1954.",
        language="en",
    )
    # 1954 is not in context (context has 1936)
    assert res.grounded is False
    assert any("1954" in m for m in res.numerical_mismatches)


def test_grounding_unsupported_factual_claim():
    """Test completely unrelated factual claim fails grounding."""
    ctx = [RetrievedChunk(chunk_id="c1", text="Paris is the capital of France.", score=0.9)]
    res = verify_grounding(
        query="What is the capital of France?",
        retrieved_chunks=ctx,
        answer="The Pacific Ocean is the largest ocean on Earth.",
        language="en",
    )
    assert res.grounded is False
    assert res.overlap_score < 0.3


def test_grounding_hindi_grounded_answer():
    """Test supported Hindi answer passes grounding."""
    ctx = [
        RetrievedChunk(
            chunk_id="c_hi",
            text="मैनहट्टन परियोजना द्वितीय विश्व युद्ध के दौरान पहला परमाणु हथियार विकसित करने का अनुसंधान था।",
            score=0.91,
        )
    ]
    res = verify_grounding(
        query="मैनहट्टन परियोजना क्या थी?",
        retrieved_chunks=ctx,
        answer="मैनहट्टन परियोजना द्वितीय विश्व युद्ध के दौरान परमाणु हथियार विकसित करने का अनुसंधान था।",
        language="hi",
    )
    assert res.grounded is True
    assert res.reason == "grounded"


def test_grounding_hindi_hallucinated_claim():
    """Test Hindi answer containing fabricated entities fails grounding."""
    ctx = [
        RetrievedChunk(
            chunk_id="c_hi",
            text="मैनहट्टन परियोजना द्वितीय विश्व युद्ध के दौरान पहला परमाणु हथियार विकसित करने का अनुसंधान था।",
            score=0.91,
        )
    ]
    res = verify_grounding(
        query="मैनहट्टन परियोजना क्या थी?",
        retrieved_chunks=ctx,
        answer="मैनहट्टन परियोजना का नेतृत्व टोक्यो में अल्बर्ट आइंस्टीन ने किया था।",
        language="hi",
    )
    assert res.grounded is False


def test_grounding_multiple_supported_claims(sample_context):
    """Test answer with multiple facts that are all present in context."""
    res = verify_grounding(
        query="What did Alan Turing do?",
        retrieved_chunks=sample_context,
        answer="In 1936, Alan Turing developed the Turing machine in England.",
        language="en",
    )
    assert res.grounded is True


def test_grounding_empty_answer_fails(sample_context):
    """Test empty and whitespace answers fail grounding validation."""
    res_empty = verify_grounding(query="Q", retrieved_chunks=sample_context, answer="")
    assert res_empty.grounded is False
    assert res_empty.reason == "empty_answer"

    res_ws = verify_grounding(query="Q", retrieved_chunks=sample_context, answer="   \n\t  ")
    assert res_ws.grounded is False


def test_grounding_measurement_normalization():
    """Test measurement normalization: 0°C == 0 degrees Celsius."""
    ctx = [RetrievedChunk(chunk_id="c1", text="Water freezes at 0 degrees Celsius.", score=0.9)]
    res = verify_grounding(
        query="What is the freezing point of water?",
        retrieved_chunks=ctx,
        answer="Water freezes at 0°C.",
        language="en",
    )
    assert res.grounded is True
    assert len(res.numerical_mismatches) == 0


def test_grounding_preserves_query_and_context(sample_context):
    """Verify original input objects remain unmodified."""
    q = "Sample query?"
    ans = "Alan Turing invented the Turing machine in 1936."
    res = verify_grounding(query=q, retrieved_chunks=sample_context, answer=ans)
    assert q == "Sample query?"
    assert len(sample_context) == 2
    assert isinstance(res, GroundingResult)
