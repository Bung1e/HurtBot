import json
import os
import uuid
from pathlib import Path

from dotenv import load_dotenv
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_community.vectorstores import AzureSearch
from langchain_openai import AzureOpenAIEmbeddings

# —————————— 1. środowisko ——————————
load_dotenv()
cfg = Path(__file__).parent / "local.settings.json"
if cfg.exists():
    data = json.loads(cfg.read_text("utf-8")).get("Values", {})
    for k, v in data.items():
        os.environ.setdefault(k, v)

REQUIRED = [
    "AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_KEY", "AZURE_OPENAI_EMBEDDING_DEPLOYMENT",
    "AZURE_SEARCH_ENDPOINT", "AZURE_SEARCH_KEY", "AZURE_SEARCH_INDEX"
]
for env in REQUIRED:
    if not os.getenv(env):
        raise ValueError(f"Brakuje {env}")

# —————————— 2. embeddingi ——————————
emb = AzureOpenAIEmbeddings(
    deployment=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT"),
    model=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    openai_api_key=os.getenv("AZURE_OPENAI_KEY"),
    openai_api_type="azure",
    openai_api_version="2023-07-01-preview",
)

# —————————— 3. JSON produktów ——————————
json_path = Path(__file__).parent / "ask_rag" / "products.json"
products = json.loads(json_path.read_text("utf-8")).get("products", [])
print("🔁 Wczytano produkty:", len(products))
prod_texts = [p.get("description","") or p.get("name","") for p in products]
prod_ids = [p["id"] for p in products]
prod_meta = [
    {"id": p["id"], "name": p["name"], "price": p.get("price")} 
    for p in products
]

# —————————— 4. PDF regulamin ——————————
pdf_path = Path(__file__).parent / "docs" / "REGULAMIN.pdf"
loader = PyMuPDFLoader(str(pdf_path))
pdf_docs = loader.load()  # zwraca listę Document
# przypisz metadata
for doc in pdf_docs:
    doc.metadata["id"] = "pdf_" + str(uuid.uuid4())
    doc.metadata["name"] = "Regulamin"
    # doc.page_content automatycznie istnieje

print("🔁 Wczytano regulamin PDF:", len(pdf_docs), "fragmentów")

# —————————— 5. Azure Search (pojedynczy indeks) ——————————
azure_search = AzureSearch(
    azure_search_endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
    azure_search_key=os.getenv("AZURE_SEARCH_KEY"),
    index_name=os.getenv("AZURE_SEARCH_INDEX"),
    embedding_function=emb,
    text_key="description",        # nazwa pola tekstowego w indeksie
    vector_field_name="embedding", # nazwa pola wektora
    document_id_key="id",
)

# —————————— 6. Indeks JSON produktów ——————————
# użyjemy upload_documents — trzeba przygotować ręcznie dokumenty
prod_vecs = emb.embed_documents(prod_texts)
prod_docs = []
for p, vec, meta in zip(products, prod_vecs, prod_meta, strict=True):
    prod_docs.append({
        "id": meta["id"],
        "name": meta["name"],
        "description": p.get("description",""),
        "embedding": vec
    })

# —————————— 7. Indeks PDF fragmentów ——————————
pdf_docs_to_upload = []
for doc in pdf_docs:
    pdf_docs_to_upload.append({
        "id": doc.metadata["id"],
        "name": doc.metadata["name"],
        "description": doc.page_content,
        "embedding": emb.embed_documents([doc.page_content])[0]
    })

# —————————— 8. Wgrywanie ——————————
all_docs = prod_docs + pdf_docs_to_upload
azure_search.client.upload_documents(documents=all_docs)
print("✅ Wgrałem:", len(all_docs), "dokumentów do Azure Search.")
