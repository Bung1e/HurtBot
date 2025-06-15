# HurtBot – B2B Intelligent Chatbot

Prosty chatbot dla hurtowni B2B, zbudowany w oparciu o Azure Cognitive Search, Azure OpenAI (lub Foundry) i interfejs Streamlit.

---

## 🚀 Gotowy prototyp

- **Backend**: Azure Function HTTP trigger (`HurtBotFunc/`).
  - Pipeline RAG: `ask_rag.py`
  - Produkty PDF, JSON → indeksowane przez `ingest_*.py`
- **Frontend**: `frontend.py` (Streamlit UI)
- **Dodatki**:
  - `utils.py` — wyszukiwanie produktów po embeddingach
  - `docs/REGULAMIN.pdf` — regulamin (może być serwowany przez Streamlit)
- **Testy**: `tests/test_azure_search.py`

---

## 🛠 Instalacja lokalna

1. Sklonuj repo:
   ```bash
   git clone https://github.com/Bung1e/HurtBot
   cd HurtBot
