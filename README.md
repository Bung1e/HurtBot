# HurtBot - Inteligentny Doradca Klienta dla Hurtowni B2B

Inteligentny asystent klienta wykorzystujący techniki RAG (Retrieval-Augmented Generation) do obsługi zapytań klientów B2B.

## Wymagania

- Python 3.12+
- pip

## Instalacja

1. Sklonuj repozytorium:
```bash
git clone https://github.com/bung1e/hurtbot.git
cd hurtbot
```

2. Zainstaluj zależności:
```bash
pip install -r requirements.txt
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
│   ├── api/               # Endpointy API
│   ├── core/              # Główna logika aplikacji
│   ├── models/            # Modele danych
│   ├── rag/               # Implementacja RAG
│   └── utils/             # Narzędzia pomocnicze
├── tests/                 # Testy
├── .github/              # Konfiguracja GitHub Actions
├── requirements.txt      # Zależności projektu
└── README.md            # Dokumentacja
