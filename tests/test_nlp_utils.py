import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.nlp_utils import classify_question

def test_classify_question_faq():
    assert classify_question("Ile mam dni na zwrot?") == "faq"

def test_classify_question_product():
    assert classify_question("Czy farba X działa na beton?") == "produkt"

def test_classify_question_empty():
    assert classify_question("") == "nieznane"
