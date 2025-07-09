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

1.  **Sklonuj repozytorium:**
    ```bash
    git clone https://github.com/Bung1e/HurtBot
    cd HurtBot
    ```

2.  **Skonfiguruj zmienne środowiskowe:**
    Utwórz plik `.env` w katalogu głównym projektu, uzupełniając swoje dane uwierzytelniające Azure OpenAI i Azure Cognitive Search.

3.  **Zbuduj i uruchom usługi:**
    ```bash
    docker-compose up --build
    ```
    Spowoduje to zbudowanie obrazów Docker i uruchomienie zarówno funkcji Azure, jak i interfejsu Chainlit. Frontend będzie dostępny pod adresem `http://localhost:8000`.
