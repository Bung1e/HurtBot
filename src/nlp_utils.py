def classify_question(question: str) -> str:
    q = question.lower()
    if any(word in q for word in ["zwrot", "reklamacja", "czas", "termin"]):
        return "faq"
    if any(word in q for word in ["farba", "produkt", "towar"]):
        return "produkt"
    if not q.strip():
        return "nieznane"
    return "inne"
