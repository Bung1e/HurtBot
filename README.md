# HurtBot – B2B Intelligent Chatbot

---

## 🚀 Gotowy prototyp (szczegółowy opis)

- **Backend**:
  - **Azure Function HTTP API** (`function_app.py`):  
    Endpoint REST `/api/ask_rag` do obsługi zapytań od frontendu.
  - **RAG Pipeline** (`src/ask_rag.py`):  
    - Rozpoznawanie typu zapytania (materiały/ogólne) przez LLM (`determine_query_type`).
    - Dla zapytań ogólnych: wyszukiwanie w Azure Cognitive Search (produkty i regulamin), generowanie odpowiedzi przez LLM.
    - Dla kalkulacji materiałów:  
      - Wyszukiwanie informacji o potrzebnych materiałach (web search przez DuckDuckGo).
      - Ekstrakcja listy materiałów i ilości przez LLM.
      - Wyszukiwanie odpowiednich produktów w indeksie produktów.
      - Generowanie odpowiedzi z podziałem na materiały podstawowe i dodatkowe.
  - **Moduły pomocnicze**:
    - `src/calc_materials.py` — logika klasyfikacji zapytań, wyszukiwania materiałów, kalkulacji i wyszukiwania produktów.
    - `src/ingest_all.py`, `src/products_index_creator` — skrypty do indeksowania produktów i dokumentów w Azure Cognitive Search.

- **Frontend**:
  - **Chainlit UI** (`src/frontend.py`):  
    - Interfejs czatu do komunikacji z botem.
    - Wysyłanie zapytań do backend API, prezentacja odpowiedzi.
    - Obsługa profili czatu i aktualizacji ustawień.

- **Dane**:
  - `data/products.json` — baza produktów do wyszukiwania i rekomendacji.
  - `data/test_qa.json` — przykładowe pytania-odpowiedzi do testów.

- **Ewaluacja i testowanie**:
  - **Testy**:  
    - `tests/test_ask_rag.py` — testy dla pipeline RAG.
    - `tests/test_nlp_utils.py` — testy dla narzędzi NLP.
  - **Ewaluacja jakości** (`eval/`):  
    - `evaluate_answers.py`, `checking_questions.py`, `generate_model_answers.py` — skrypty do automatycznej oceny i analizy jakości odpowiedzi.
    - `model_answers.json`, `scored_answers.json`, `result.json` — wyniki i odpowiedzi wzorcowe.

- **Infrastruktura**:
  - `docker-compose.yml` — uruchamianie Azure Function i Chainlit UI w kontenerach.
  - `pyproject.toml`, `uv.lock` — zależności Pythona.
  - `.env`, `local.settings.json` — zmienne środowiskowe dla Azure i kluczy API.

---

## 🛠 Instalacja lokalna

1.  **Sklonuj repozytorium:**
    ```bash
    git clone https://github.com/Bung1e/HurtBot
    cd HurtBot
    ```

2.  **Skonfiguruj zmienne środowiskowe:**
    Utwórz plik `.env`(patrz .env.example) w katalogu głównym projektu, uzupełniając swoje dane uwierzytelniające Azure OpenAI i Azure Cognitive Search.

3.  **Zbuduj i uruchom usługi:**
    ```bash
    docker-compose up --build
    ```
    Spowoduje to zbudowanie obrazów Docker i uruchomienie zarówno funkcji Azure, jak i interfejsu Chainlit. Frontend będzie dostępny pod adresem `http://localhost:8000`.
