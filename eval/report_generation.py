import matplotlib.pyplot as plt
import pandas as pd
from typing import Any

plik: str = "eval/result.json"
df: pd.DataFrame = pd.read_json(plik)

n_product: int = 15
df["grupa"] = ["produkty"] * n_product + ["regulamin"] * (len(df) - n_product)

srednia_wszystko: float = df["semantic_similarity"].mean()
srednia_produkty: float = df[df["grupa"] == "produkty"]["semantic_similarity"].mean()
srednia_regulamin: float = df[df["grupa"] == "regulamin"]["semantic_similarity"].mean()


plt.figure(figsize=(10, 5))
plt.hist(
    df[df["grupa"] == "produkty"]["semantic_similarity"],
    bins=10,
    alpha=0.7,
    label="Produkty",
)
plt.hist(
    df[df["grupa"] == "regulamin"]["semantic_similarity"],
    bins=10,
    alpha=0.7,
    label="Regulamin/Ogólne",
)
plt.xlabel("Semantic Similarity")
plt.ylabel("Liczba odpowiedzi")
plt.title("Rozkład semantic_similarity dla grup pytań")
plt.legend()
plt.tight_layout()
plt.savefig("semantic_similarity_hist.png")
plt.show()

plt.figure(figsize=(6, 5))
df.boxplot(column="semantic_similarity", by="grupa")
plt.title("Semantic Similarity wg grupy pytania")
plt.suptitle("")
plt.ylabel("Semantic Similarity")
plt.savefig("semantic_similarity_boxplot.png")
plt.show()
