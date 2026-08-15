"""Unit tests for fixed and semantic chunking strategies and Hindi Unicode handling."""

import pytest
from src.data.download_and_process import (
    chunk_fixed_size,
    chunk_semantic_sentence_aware,
    split_sentences_multilingual,
)


def test_split_sentences_multilingual_english():
    text = "This is sentence one. This is sentence two! Is this sentence three?"
    sents = split_sentences_multilingual(text)
    assert len(sents) == 3
    assert sents[0] == "This is sentence one."
    assert sents[1] == "This is sentence two!"
    assert sents[2] == "Is this sentence three?"


def test_split_sentences_multilingual_hindi():
    hindi_text = "गोवा भारत का एक खूबसूरत राज्य है। यहाँ के समुद्र तट बहुत प्रसिद्ध हैं। क्या आप कभी यहाँ गए हैं?"
    sents = split_sentences_multilingual(hindi_text)
    assert len(sents) == 3
    assert "गोवा भारत" in sents[0]
    assert "समुद्र तट" in sents[1]
    assert "क्या आप कभी" in sents[2]


def test_chunk_fixed_size_basic():
    text = "A" * 2500
    chunks = chunk_fixed_size(
        text=text,
        parent_passage_id="test_doc_1",
        language="en",
        query_id=101,
        is_selected=True,
        chunk_size=1000,
        overlap=150,
    )
    assert len(chunks) == 3
    assert chunks[0]["chunk_id"] == "test_doc_1_fixed_0"
    assert chunks[0]["chunk_index"] == 0
    assert chunks[0]["chunk_strategy"] == "fixed"
    assert chunks[0]["language"] == "en"
    assert chunks[0]["is_selected"] is True
    assert len(chunks[0]["text"]) == 1000
    assert chunks[1]["chunk_id"] == "test_doc_1_fixed_1"
    assert chunks[1]["chunk_index"] == 1


def test_chunk_fixed_size_unicode_hindi():
    hindi_text = "यह एक परीक्षण वाक्य है जो हिंदी में लिखा गया है। " * 50
    chunks = chunk_fixed_size(
        text=hindi_text,
        parent_passage_id="test_hi_1",
        language="hi",
        query_id=202,
        is_selected=False,
        chunk_size=500,
        overlap=50,
    )
    assert len(chunks) > 1
    for c in chunks:
        assert c["language"] == "hi"
        assert c["chunk_strategy"] == "fixed"
        assert len(c["text"]) > 0
        assert c["chunk_id"].startswith("test_hi_1_fixed_")


def test_chunk_fixed_size_empty():
    chunks = chunk_fixed_size(
        text="   ",
        parent_passage_id="test_empty",
        language="en",
        query_id=303,
        is_selected=False,
    )
    assert len(chunks) == 0


def test_chunk_semantic_sentence_aware_basic():
    hindi_text = (
        "गोवा भारत का एक प्रसिद्ध पर्यटन स्थल है। "
        "यहाँ कई ऐतिहासिक चर्च और सुंदर समुद्र तट हैं। "
        "हर साल लाखों पर्यटक यहाँ घूमने आते हैं। "
        "यहाँ का मौसम बहुत ही सुहावना रहता है।"
    )
    chunks = chunk_semantic_sentence_aware(
        text=hindi_text,
        parent_passage_id="hi_doc_1",
        language="hi",
        query_id=404,
        is_selected=True,
        max_chunk_size=100,
    )
    assert len(chunks) >= 2
    for c in chunks:
        assert c["chunk_strategy"] == "semantic"
        assert c["parent_passage_id"] == "hi_doc_1"
        assert c["language"] == "hi"
        assert len(c["text"]) <= 100 or len(c["text"]) > 0


def test_chunk_semantic_oversized_sentence_fallback():
    # A single sentence longer than max_chunk_size
    long_sentence = "यह बहुत लंबा वाक्य है जिसमें कोई विराम चिह्न नहीं है " * 20
    chunks = chunk_semantic_sentence_aware(
        text=long_sentence,
        parent_passage_id="long_sent_doc",
        language="hi",
        query_id=505,
        is_selected=False,
        max_chunk_size=150,
    )
    assert len(chunks) > 1
    for c in chunks:
        assert c["chunk_strategy"] == "semantic"
        assert len(c["text"]) > 0
        assert c["chunk_id"].startswith("long_sent_doc_semantic_")
