import json
from typing import Any

from tqdm import tqdm

from ask_rag import ask_rag

with open("data/test_qa.json", encoding="utf-8") as f:
    qa_data: list[dict[str, Any]] = json.load(f)

results: list[dict[str, str]] = []
for item in tqdm(qa_data, desc="Generating model answers"):
    question: str = item["question"]
    expected_answer: str = item["expected_answer"]
    try:
        model_answer: str = ask_rag(question)
    except Exception as e:
        model_answer = f"[ERROR] {e}"
    results.append(
        {
            "question": question,
            "expected_answer": expected_answer,
            "model_answer": model_answer,
        }
    )

with open("eval/model_answers.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
