import os
import json
from pathlib import Path
from azure.core.credentials import AzureKeyCredential
from langchain_openai import AzureOpenAIEmbeddings
from langchain_community.vectorstores import AzureSearch

# 1. Wczytaj zmienne (opcjonalnie z local.settings.json)
cfg = Path(__file__).parent / "local.settings.json"
if cfg.exists():
    cfg_data = json.loads(cfg.read_text("utf-8")).get("Values", {})
    for k, v in cfg_data.items():
        os.environ.setdefault(k, v)

# 2. Wymagane zmienne
for name in ["AZURE_OPENAI_ENDPOINT","AZURE_OPENAI_KEY","AZURE_OPENAI_EMBEDDING_DEPLOYMENT",
             "AZURE_SEARCH_ENDPOINT","AZURE_SEARCH_KEY","AZURE_SEARCH_INDEX"]:
    if not os.getenv(name):
        raise ValueError(f"Brakuje zmiennej środowiskowej: {name}")

# 3. Wczytaj JSON
DATA_PATH = Path(__file__).parent / "ask_rag" / "products.json"
if not DATA_PATH.exists():
    raise FileNotFoundError(f"Nie znaleziono: {DATA_PATH}")
products = json.loads(DATA_PATH.read_text("utf-8")).get("products", [])
print(f"🔁 Wczytano {len(products)} produktów.")

# 4. Embeddingi
emb = AzureOpenAIEmbeddings(
    deployment=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT"),
    model=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    openai_api_key=os.getenv("AZURE_OPENAI_KEY"),
    openai_api_type="azure",
    openai_api_version="2023-07-01-preview",
)

# 5. Przygotuj dokumenty
texts = [p.get("description","") for p in products]
embeddings = emb.embed_documents(texts)
docs = []
for p, vec in zip(products, embeddings):
    docs.append({
        "id": p["id"],
        "name": p["name"],
        "description": p.get("description",""),
        "embedding": vec
    })
print(f"🔁 Przygotowano {len(docs)} dokumentów.")

# 6. Połącz z Azure Cognitive Search
azure_search = AzureSearch(
    azure_search_endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
    azure_search_key=os.getenv("AZURE_SEARCH_KEY"),
    index_name=os.getenv("AZURE_SEARCH_INDEX"),
    embedding_function=emb,
    text_key="description",
    vector_field_name="embedding",
    document_id_key="id",
)

# 7. Wyślij dokumenty
azure_search.client.upload_documents(documents=docs)
print("✅ Zaindeksowano dokumenty w Azure Cognitive Search.")
