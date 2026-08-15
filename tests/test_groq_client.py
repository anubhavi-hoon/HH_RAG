"""Unit tests for Groq LLM generation module (using mocks)."""

from unittest.mock import MagicMock, patch
import pytest
import groq

from src.llm.groq_client import (
    format_context_chunks,
    generate_answer,
    get_groq_client,
    SYSTEM_PROMPT,
)


@pytest.fixture
def sample_retrieved_chunks():
    return [
        {
            "rank": 1,
            "chunk_id": "chunk_en_1",
            "text": "Alan Turing invented the Turing machine in 1936.",
            "language": "en",
            "score": 0.9123,
        },
        {
            "rank": 2,
            "chunk_id": "chunk_hi_2",
            "text": "ट्यूरिंग मशीन की खोज एलन ट्यूरिंग ने की थी।",
            "language": "hi",
            "score": 0.8541,
        },
    ]


def test_format_context_chunks(sample_retrieved_chunks):
    """Test formatting of retrieved chunks into compact prompt context."""
    formatted = format_context_chunks(sample_retrieved_chunks)
    assert "[CONTEXT 1]" in formatted
    assert "Language: en" in formatted
    assert "Similarity: 0.91" in formatted
    assert "Alan Turing invented the Turing machine" in formatted
    assert "[CONTEXT 2]" in formatted
    assert "Language: hi" in formatted
    assert "Similarity: 0.85" in formatted
    assert "ट्यूरिंग मशीन" in formatted


def test_generate_answer_success(sample_retrieved_chunks):
    """Test successful answer generation with mocked Groq client."""
    mock_client = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "Alan Turing invented the Turing machine in 1936."
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_response

    result = generate_answer(
        question="Who invented the Turing machine?",
        retrieved_chunks=sample_retrieved_chunks,
        model_name="openai/gpt-oss-20b",
        client=mock_client,
    )

    assert result["answer"] == "Alan Turing invented the Turing machine in 1936."
    assert result["model"] == "openai/gpt-oss-20b"
    assert isinstance(result["llm_latency_ms"], float)
    assert result["llm_latency_ms"] >= 0.0
    assert result["retrieved_chunks"] == sample_retrieved_chunks

    # Verify mock was called with correct parameters
    mock_client.chat.completions.create.assert_called_once()
    call_kwargs = mock_client.chat.completions.create.call_args.kwargs
    assert call_kwargs["model"] == "openai/gpt-oss-20b"
    assert call_kwargs["temperature"] == 0.0
    assert len(call_kwargs["messages"]) == 2
    assert call_kwargs["messages"][0]["role"] == "system"
    assert call_kwargs["messages"][0]["content"] == SYSTEM_PROMPT
    assert "CONTEXT:" in call_kwargs["messages"][1]["content"]
    assert "USER QUESTION:\nWho invented the Turing machine?" in call_kwargs["messages"][1]["content"]


def test_generate_answer_empty_response(sample_retrieved_chunks):
    """Test handling when Groq API returns empty content or choices."""
    mock_client = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "   "
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_response

    with pytest.raises(RuntimeError, match="empty response text"):
        generate_answer(
            question="What is this?",
            retrieved_chunks=sample_retrieved_chunks,
            client=mock_client,
        )


def test_generate_answer_api_error(sample_retrieved_chunks):
    """Test handling of Groq API error and generic exceptions."""
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = groq.APIConnectionError(
        request=MagicMock()
    )

    with pytest.raises(RuntimeError, match="Groq API error"):
        generate_answer(
            question="What is this?",
            retrieved_chunks=sample_retrieved_chunks,
            client=mock_client,
        )

    # Test generic unexpected exception
    mock_client.chat.completions.create.side_effect = Exception("Unexpected backend fault")
    with pytest.raises(RuntimeError, match="LLM generation failed"):
        generate_answer(
            question="What is this?",
            retrieved_chunks=sample_retrieved_chunks,
            client=mock_client,
        )



def test_missing_api_key(sample_retrieved_chunks, monkeypatch):
    """Test that missing GROQ_API_KEY raises a clean ValueError without crashing."""
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with pytest.raises(ValueError, match="GROQ_API_KEY is not set"):
        get_groq_client(api_key=None)


def test_input_validation(sample_retrieved_chunks):
    """Test input validation for question and retrieved chunks."""
    # Empty question
    with pytest.raises(ValueError, match="Question cannot be empty"):
        generate_answer("", sample_retrieved_chunks, client=MagicMock())

    with pytest.raises(ValueError, match="Question cannot be empty"):
        generate_answer("   ", sample_retrieved_chunks, client=MagicMock())

    # Invalid question type
    with pytest.raises(ValueError, match="Question must be a string"):
        generate_answer(None, sample_retrieved_chunks, client=MagicMock())

    # Empty retrieved chunks
    with pytest.raises(ValueError, match="Retrieved chunks must be a non-empty list"):
        generate_answer("Valid question?", [], client=MagicMock())

    with pytest.raises(ValueError, match="Retrieved chunks must be a non-empty list"):
        generate_answer("Valid question?", None, client=MagicMock())
