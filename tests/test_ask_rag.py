# tests/test_ask_rag.py
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from ask_rag import ask_rag

def test_ask_rag_output():
    answer = ask_rag("Czy mogę zwrócić towar?")
    assert isinstance(answer, str)
    assert len(answer) > 0
