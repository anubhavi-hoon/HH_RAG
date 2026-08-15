#!/usr/bin/env python3
"""
Groq LLM Generation Client for Multilingual RAG.
Project: HH Goa 2026 Voice-Enabled Multilingual RAG System.

Formats retrieved context chunks, builds grounded prompts, and generates
answers via Groq API.
"""

import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
import groq

# Load environment variables from .env if present
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("groq_client")


DEFAULT_GROQ_MODEL = "openai/gpt-oss-20b"

SYSTEM_PROMPT = """You are a grounded RAG assistant.
Use the provided retrieved context to answer the user's question accurately and concisely.
Prefer the retrieved context over unsupported outside knowledge.
Do not invent facts or extrapolate beyond what the context supports.
If the context does not contain enough information to answer the question, clearly state that the available context is insufficient.
Respond in the same language as the user's question when possible.
Do not mention prompt formatting or internal implementation details.
Do not fabricate citations."""


def format_context_chunks(retrieved_chunks: List[Dict[str, Any]]) -> str:
    """
    Formats retrieved chunks into a clean, compact context block.
    """
    context_blocks = []
    for idx, chunk in enumerate(retrieved_chunks, start=1):
        language = chunk.get("language", "unknown")
        score = chunk.get("score", 0.0)
        text = (chunk.get("text") or "").strip()
        context_blocks.append(
            f"[CONTEXT {idx}]\n"
            f"Language: {language}\n"
            f"Similarity: {score:.2f}\n"
            f"Text:\n{text}"
        )
    return "\n\n".join(context_blocks)


def get_groq_client(api_key: Optional[str] = None) -> groq.Groq:
    """
    Initializes and returns a Groq client instance.
    """
    key = api_key or os.environ.get("GROQ_API_KEY")
    if not key or not key.strip():
        raise ValueError(
            "GROQ_API_KEY is not set. Please set the GROQ_API_KEY environment variable or configure it in a .env file."
        )
    return groq.Groq(api_key=key.strip())


def generate_answer(
    question: str,
    retrieved_chunks: List[Dict[str, Any]],
    model_name: Optional[str] = None,
    max_tokens: Optional[int] = None,
    api_key: Optional[str] = None,
    client: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Generates a grounded answer to the user's question using retrieved context chunks via Groq.

    Args:
        question: User query string (non-empty).
        retrieved_chunks: Non-empty list of retrieved chunk dictionaries.
        model_name: Optional Groq model name override (defaults to GROQ_MODEL env var or 'openai/gpt-oss-20b').
        max_tokens: Optional max tokens limit for generated completion.
        api_key: Optional API key override.
        client: Optional pre-initialized Groq client (useful for unit testing and mocking).

    Returns:
        Structured dictionary with answer, model, latency, token usage, and preserved retrieved chunks.
    """
    # 1. Validate question
    if not isinstance(question, str):
        raise ValueError("Question must be a string.")
    clean_question = question.strip()
    if not clean_question:
        raise ValueError("Question cannot be empty or whitespace-only.")

    # 2. Validate retrieved_chunks
    if not isinstance(retrieved_chunks, list) or len(retrieved_chunks) == 0:
        raise ValueError("Retrieved chunks must be a non-empty list of chunk dictionaries.")

    # 3. Determine model name
    effective_model = model_name or os.environ.get("GROQ_MODEL") or DEFAULT_GROQ_MODEL

    # 4. Format context and construct prompt
    formatted_context = format_context_chunks(retrieved_chunks)
    user_prompt = f"CONTEXT:\n{formatted_context}\n\nUSER QUESTION:\n{clean_question}"

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    # 5. Initialize client
    groq_client = client or get_groq_client(api_key=api_key)

    # 6. Call Groq API measuring latency
    t_start = time.perf_counter()
    call_kwargs: Dict[str, Any] = {
        "model": effective_model,
        "messages": messages,
        "temperature": 0.0,
    }
    if max_tokens is not None:
        call_kwargs["max_tokens"] = max_tokens

    try:
        response = groq_client.chat.completions.create(**call_kwargs)
    except groq.AuthenticationError as e:
        logger.error(f"Groq API authentication failure: {e}")
        raise RuntimeError("Groq API authentication failed. Check GROQ_API_KEY.") from e
    except groq.RateLimitError as e:
        logger.error(f"Groq API rate limit exceeded: {e}")
        raise RuntimeError("Groq API rate limit exceeded. Please try again later.") from e
    except groq.APITimeoutError as e:
        logger.error(f"Groq API request timed out: {e}")
        raise RuntimeError("Groq API request timed out.") from e
    except groq.APIError as e:
        logger.error(f"Groq API returned an error: {e}")
        raise RuntimeError(f"Groq API error: {e.message}") from e
    except Exception as e:
        logger.error(f"Unexpected error during Groq completion: {e}")
        raise RuntimeError(f"LLM generation failed: {str(e)}") from e

    t_end = time.perf_counter()
    llm_latency_ms = (t_end - t_start) * 1000.0

    # 7. Extract answer
    if not response.choices or len(response.choices) == 0:
        raise RuntimeError("Groq API returned an empty choices list.")

    answer_content = response.choices[0].message.content or ""
    answer_text = answer_content.strip()

    if not answer_text:
        raise RuntimeError("Groq API returned an empty response text.")

    # 8. Extract token usage if available
    usage_info = {}
    if hasattr(response, "usage") and response.usage:
        usage_info = {
            "prompt_tokens": getattr(response.usage, "prompt_tokens", None),
            "completion_tokens": getattr(response.usage, "completion_tokens", None),
            "total_tokens": getattr(response.usage, "total_tokens", None),
        }

    return {
        "answer": answer_text,
        "model": effective_model,
        "llm_latency_ms": round(llm_latency_ms, 2),
        "usage": usage_info,
        "retrieved_chunks": retrieved_chunks,
    }



def run_smoke_tests():
    """
    Executes live smoke tests with real retrieval for English and Hindi questions.
    """
    from src.retrieval.retriever import retrieve_chunks

    test_queries = [
        ("English", "What is artificial intelligence?"),
        ("Hindi", "कृत्रिम बुद्धिमत्ता क्या है?"),
    ]

    print("\n" + "=" * 50)
    print("STAGE 4 GROQ LLM SMOKE TESTS")
    print("=" * 50)

    model_name = os.environ.get("GROQ_MODEL") or DEFAULT_GROQ_MODEL

    results = []
    for lang, q in test_queries:
        print(f"\nRunning {lang} Smoke Test...")
        print(f"Question:\n{q}\n")

        # 1. Retrieve chunks
        t_ret_start = time.perf_counter()
        chunks = retrieve_chunks(q, top_k=5)
        t_ret_end = time.perf_counter()
        ret_latency_ms = (t_ret_end - t_ret_start) * 1000.0

        print(f"Retrieved chunks: {len(chunks)}")
        print(f"Top 1 chunk ID: {chunks[0]['chunk_id']} (score: {chunks[0]['score']:.4f})")
        print(f"Retrieval latency: {ret_latency_ms:.2f} ms")

        # 2. Generate answer
        try:
            res = generate_answer(q, chunks, model_name=model_name)
            print(f"\nLLM answer:\n{res['answer']}\n")
            print(f"Model:\n{res['model']}")
            print(f"LLM latency:\n{res['llm_latency_ms']:.2f} ms")
            print(f"Status:\nPASS")
            results.append((lang, True, res["llm_latency_ms"], res["answer"]))
        except Exception as e:
            print(f"LLM generation failed: {e}")
            print(f"Status:\nFAIL")
            results.append((lang, False, 0.0, str(e)))

    print("\n" + "=" * 50)
    return results


if __name__ == "__main__":
    if not os.environ.get("GROQ_API_KEY"):
        print("ERROR: GROQ_API_KEY is not set.")
        print("Please set GROQ_API_KEY in your environment or .env file before running smoke tests.")
        sys.exit(1)

    run_smoke_tests()
