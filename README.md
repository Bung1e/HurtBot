# HurtBot - Inteligentny Doradca Klienta dla Hurtowni B2B

Inteligentny asystent klienta wykorzystujący techniki RAG (Retrieval-Augmented Generation) do obsługi zapytań klientów B2B.

## Wymagania

- Python 3.12+
- UV (Ultrafast Python Package Installer)

## Instalacja

1. Sklonuj repozytorium:
```bash
git clone https://github.com/bung1e/hurtbot.git
cd hurtbot
```

2. Zainstaluj UV (jeśli nie jest zainstalowany):
```bash
pip install uv
```

3. Utwórz wirtualne środowisko i zainstaluj zależności:
```bash
uv venv
source .venv/bin/activate  # dla Linux/Mac
# lub
.venv\Scripts\activate  # dla Windows
uv pip install -e .
```

## Uruchomienie

Aby uruchomić aplikację:

```bash
streamlit run src/app.py
```

## Struktura projektu

```
hurtbot/
├── src/                    # Kod źródłowy
│   ├── __init__.py        # Inicjalizacja pakietu
│   ├── api.py             # FastAPI endpointy
│   └── app.py             # Aplikacja Streamlit
├── tests/                 # Testy
│   └── test_basic.py      # Podstawowe testy
├── .github/              # Konfiguracja GitHub Actions
├── pyproject.toml        # Zależności i konfiguracja projektu
└── README.md            # Dokumentacja
