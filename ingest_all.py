<<<<<<< HEAD
=======
# ingest_all.py

>>>>>>> refactor-rag-structure
import json
import os
import uuid
from pathlib import Path
<<<<<<< HEAD

from dotenv import load_dotenv
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_community.vectorstores import AzureSearch
from langchain_openai import AzureOpenAIEmbeddings
=======
>>>>>>> refactor-rag-structure

from dotenv import load_dotenv
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_community.vectorstores import AzureSearch
from langchain_openai import AzureOpenAIEmbeddings

# 1. Wczytywanie zmiennych środowiskowych
cfg = Path(__file__).parent / "local.settings.json"
if cfg.exists():
    data = json.loads(cfg.read_text("utf-8")).get("Values", {})
    for k, v in data.items():
        os.environ.setdefault(k, v)

<<<<<<< HEAD
REQUIRED = [
    "AZURE_OPENAI_ENDPOINT",
    "AZURE_OPENAI_KEY",
    "AZURE_OPENAI_EMBEDDING_DEPLOYMENT",
    "AZURE_SEARCH_ENDPOINT",
    "AZURE_SEARCH_KEY",
    "AZURE_SEARCH_INDEX",
]
for env in REQUIRED:
    if not os.getenv(env):
        raise ValueError(f"Brakuje {env}")
=======
load_dotenv()
>>>>>>> refactor-rag-structure

required = [
    "AZURE_OPENAI_ENDPOINT",
    "AZURE_OPENAI_KEY",
    "AZURE_OPENAI_EMBEDDING_DEPLOYMENT",
    "AZURE_SEARCH_ENDPOINT",
    "AZURE_SEARCH_KEY",
]
for env in required:
    if not os.getenv(env):
        raise ValueError(f"Brakuje zmiennej {env}")

# 2. Embeddingi
emb = AzureOpenAIEmbeddings(
    deployment=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT"),
    model=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    openai_api_key=os.getenv("AZURE_OPENAI_KEY"),
    openai_api_type="azure",
    openai_api_version="2023-07-01-preview",
)

<<<<<<< HEAD
# —————————— 3. JSON produktów ——————————
json_path = Path(__file__).parent / "ask_rag" / "products.json"
products = json.loads(json_path.read_text("utf-8")).get("products", [])
print("🔁 Wczytano produkty:", len(products))
prod_texts = [p.get("description", "") or p.get("name", "") for p in products]
prod_ids = [p["id"] for p in products]
prod_meta = [
    {"id": p["id"], "name": p["name"], "price": p.get("price")} for p in products
]
=======
# 3. Wczytanie produktów
products_path = Path(__file__).parent / "ask_rag" / "products.json"
products = json.loads(products_path.read_text("utf-8"))
>>>>>>> refactor-rag-structure

prod_docs = []
for p in products:
    content = " ".join(
        [
            p.get("name", ""),
            p.get("description", ""),
            p.get("content", ""),
            f"Cena: {p.get('price', 'brak ceny')} PLN",
        ]
    )
    embedding = emb.embed_documents([content])[0]
    prod_docs.append(
        {
            "id": p["id"],
            "name": p.get("name", ""),
            "description": p.get("description", ""),
            "content": content,
            "category": p.get("category", "brak"),
            "embedding": embedding,
        }
    )

print(f"🔁 Wczytano {len(prod_docs)} produktów")

# 4. Wczytanie PDF i embedding
pdf_path = Path(__file__).parent / "docs" / "REGULAMIN.pdf"
loader = PyMuPDFLoader(str(pdf_path))
pdf_docs = loader.load()

pdf_docs_to_upload = []
for doc in pdf_docs:
    doc.metadata["id"] = "pdf_" + str(uuid.uuid4())
    content = doc.page_content
    embedding = emb.embed_documents([content])[0]
    pdf_docs_to_upload.append(
        {
            "id": doc.metadata["id"],
            "filename": "REGULAMIN.pdf",
            "content": content,
            "embedding": embedding,
        }
    )

print(f"📄 Wczytano {len(pdf_docs_to_upload)} fragmentów PDF")

# 5. Upload do Azure Search
azure_products = AzureSearch(
    azure_search_endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
    azure_search_key=os.getenv("AZURE_SEARCH_KEY"),
    index_name="products-index",
    embedding_function=emb,
<<<<<<< HEAD
    text_key="description",  # nazwa pola tekstowego w indeksie
    vector_field_name="embedding",  # nazwa pola wektora
    document_id_key="id",
)

# —————————— 6. Indeks JSON produktów ——————————
# użyjemy upload_documents — trzeba przygotować ręcznie dokumenty
prod_vecs = emb.embed_documents(prod_texts)
prod_docs = []
for p, vec, meta in zip(products, prod_vecs, prod_meta, strict=True):
    prod_docs.append(
        {
            "id": meta["id"],
            "name": meta["name"],
            "description": p.get("description", ""),
            "embedding": vec,
        }
    )

# —————————— 7. Indeks PDF fragmentów ——————————
pdf_docs_to_upload = []
for doc in pdf_docs:
    pdf_docs_to_upload.append(
        {
            "id": doc.metadata["id"],
            "name": doc.metadata["name"],
            "description": doc.page_content,
            "embedding": emb.embed_documents([doc.page_content])[0],
        }
    )
=======
    text_key="content",
    vector_field_name="embedding",
    document_id_key="id",
)

azure_regulamin = AzureSearch(
    azure_search_endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
    azure_search_key=os.getenv("AZURE_SEARCH_KEY"),
    index_name="regulamin-index",
    embedding_function=emb,
    text_key="content",
    vector_field_name="embedding",
    document_id_key="id",
)

azure_products.client.upload_documents(prod_docs)
azure_regulamin.client.upload_documents(pdf_docs_to_upload)
>>>>>>> refactor-rag-structure

print("✅ Dokumenty zaindeksowane.")
