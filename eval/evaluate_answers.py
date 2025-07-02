import json
from typing import Any

import pandas as pd
from prompttools.utils import semantic_similarity
from tqdm import tqdm

with open("eval/model_answers.json", encoding="utf-8") as f:
    data: list[dict[str, Any]] = json.load(f)

df: pd.DataFrame = pd.DataFrame(data)


def eval_row(row: pd.Series) -> dict[str, float]:
    semsim: float = semantic_similarity(
        row, row["expected_answer"], response_column_name="model_answer"
    )
    return {"semantic_similarity": semsim}


results: list[dict[str, float]] = [
    eval_row(row) for _, row in tqdm(df.iterrows(), total=len(df))
]

results_df: pd.DataFrame = pd.DataFrame(results)
df = pd.concat([df, results_df], axis=1)

df.to_json("eval/result.json", orient="records", force_ascii=False, indent=2)

with open("eval/model_answers.json", encoding="utf-8") as f:
    data: list[dict[str, Any]] = json.load(f)

df: pd.DataFrame = pd.DataFrame(data)


def eval_row(row: pd.Series) -> dict[str, float]:
    
    semsim: float = semantic_similarity(
        row, row["expected_answer"], response_column_name="model_answer"
    )
    return {
        
        "semantic_similarity": semsim
    }


results: list[dict[str, float]] = [
    eval_row(row) for _, row in tqdm(df.iterrows(), total=len(df))
]

results_df: pd.DataFrame = pd.DataFrame(results)
df = pd.concat([df, results_df], axis=1)

df.to_json("eval/result.json", orient="records", force_ascii=False, indent=2)
