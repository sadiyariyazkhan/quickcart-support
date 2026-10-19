import pytest
import json
from app import rag

def load_questions():
    with open("test/rag_questions.json", "r", encoding="utf-8") as f:
        return json.load(f)

@pytest.mark.parametrize("q", load_questions())
def test_rag_citations(q):
    res = rag.answer(q["question"])
    
    if q["expected_section"] is None:
        assert res["refused"] is True
    else:
        assert res["refused"] is False
        # Check if the expected section is in the returned citations
        found_sections = [c["section"] for c in res["citations"]]
        assert q["expected_section"] in found_sections