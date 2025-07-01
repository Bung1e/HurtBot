import json
from pathlib import Path

from langchain_azure_ai.chat_models import AzureAIChatCompletionsModel

# ——————————————————————————————————————————
# 1. Wczytaj dane z local.settings.json
# ——————————————————————————————————————————
settings_path = Path(__file__).resolve().parents[1] / "local.settings.json"
with open(settings_path, encoding="utf-8") as f:
    settings = json.load(f)["Values"]

AZURE_FOUNDRY_ENDPOINT = settings["AZURE_FOUNDRY_ENDPOINT"]
AZURE_FOUNDRY_KEY = settings["AZURE_FOUNDRY_KEY"]
AZURE_OPENAI_CHAT_DEPLOYMENT = settings["AZURE_OPENAI_CHAT_DEPLOYMENT"]

# ——————————————————————————————————————————
# 2. Konfiguracja modelu czatu (Foundry)
# ——————————————————————————————————————————
llm = AzureAIChatCompletionsModel(
    endpoint=AZURE_FOUNDRY_ENDPOINT,
    credential=AZURE_FOUNDRY_KEY,
    model=AZURE_OPENAI_CHAT_DEPLOYMENT,
    temperature=0.0,
)


# ——————————————————————————————————————————
# 3. Funkcja oceniająca odpowiedź modelu
# ——————————————————————————————————————————
def score_answer(expected: str, model: str) -> float:
    prompt = f"""
Oceń jakość odpowiedzi modelu w porównaniu do oczekiwanej odpowiedzi.

### Oczekiwana odpowiedź:
{expected}

### Odpowiedź modelu:
{model}

### Zadanie:
Oceń zgodność i trafność odpowiedzi modelu względem oczekiwanej 
odpowiedzi w skali od 0.0 do 1.0.
Zwróć tylko liczbę zmiennoprzecinkową.

Odpowiedź:
"""

    response = llm.invoke(prompt)
    try:
        score = float(response.content.strip())
        return max(0.0, min(1.0, score))
    except Exception as e:
        print("Błąd parsowania:", e)
        return 0.0


# ——————————————————————————————————————————
# 4. Główna pętla oceniająca wszystkie odpowiedzi
# ——————————————————————————————————————————
def main():
    with open("model_answers.json", encoding="utf-8") as f:
        data = json.load(f)

    results = []
    for entry in data:
        expected = entry["expected_answer"]
        model = entry["model_answer"]
        score = score_answer(expected, model)
        entry["score"] = score
        results.append(entry)
        print(f"Pytanie: {entry['question']}\nOcena: {score:.2f}\n")

    with open("scored_answers.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
