import json
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain.chains import RetrievalQA
from langchain_azure_ai.chat_models import AzureAIChatCompletionsModel
from langchain_community.retrievers import AzureAISearchRetriever

# 1️⃣ Wczytanie .env i local.settings.json
load_dotenv()
cfg = Path(__file__).parent / "local.settings.json"
if cfg.exists():
    data = json.loads(cfg.read_text(encoding="utf-8")).get("Values", {})
    for k, v in data.items():
        os.environ.setdefault(k, v)

# 2️⃣ Wydruki debugujące
print("OPENAI_CHAT_DEPLOYMENT:", os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT"))
print("OPENAI_ENDPOINT:", os.getenv("AZURE_OPENAI_ENDPOINT"))
print("OPENAI_KEY ok?:", bool(os.getenv("AZURE_OPENAI_KEY")))
print("SEARCH_ENDPOINT:", os.getenv("AZURE_SEARCH_ENDPOINT"))
print("SEARCH_KEY ok?:", bool(os.getenv("AZURE_SEARCH_KEY")))
print("SEARCH_INDEX:", os.getenv("AZURE_SEARCH_INDEX"))
print("FOUNDRY_ENDPOINT:", os.getenv("AZURE_FOUNDRY_ENDPOINT"))
print("FOUNDRY_KEY ok?:", bool(os.getenv("AZURE_FOUNDRY_KEY")))

# 3️⃣ Weryfikacja zmiennych środowiskowych
required = [
    "AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_KEY", "AZURE_OPENAI_CHAT_DEPLOYMENT",
    "AZURE_SEARCH_ENDPOINT", "AZURE_SEARCH_KEY", "AZURE_SEARCH_INDEX",
    "AZURE_FOUNDRY_ENDPOINT", "AZURE_FOUNDRY_KEY"
]
missing = [v for v in required if not os.getenv(v)]
if missing:
    raise ValueError(f"Brakuje zmiennej(y): {', '.join(missing)}")

# 4️⃣ Konfiguracja retrievera Azure Search
search_svc = os.getenv("AZURE_SEARCH_ENDPOINT").split("//")[-1].split(".")[0]
os.environ["AZURE_AI_SEARCH_SERVICE_NAME"] = search_svc
os.environ["AZURE_AI_SEARCH_INDEX_NAME"] = os.getenv("AZURE_SEARCH_INDEX")
os.environ["AZURE_AI_SEARCH_API_KEY"] = os.getenv("AZURE_SEARCH_KEY")

# 5️⃣ Import potrzebnych komponentów
def ask_rag(query: str) -> str:
    retriever = AzureAISearchRetriever(
        content_key="description",
        index_name=os.getenv("AZURE_SEARCH_INDEX"),
        top_k=3
    )
    llm = AzureAIChatCompletionsModel(
        endpoint=os.getenv("AZURE_FOUNDRY_ENDPOINT"),
        credential=os.getenv("AZURE_FOUNDRY_KEY"),
        model=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT"),
        temperature=0.0
    )
    chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        return_source_documents=False
    )
    res = chain.invoke({"query": query})
    return res.get("result") or res.get("answer") or ""

if __name__ == "__main__":
    q = input("Pytanie: ")
    odp = ask_rag(q)
    print("\n🧠 Odpowiedź:", odp)
