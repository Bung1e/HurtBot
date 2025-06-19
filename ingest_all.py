# ingest_all.py

import os
import json
import uuid
from pathlib import Path
from dotenv import load_dotenv
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_openai import AzureOpenAIEmbeddings
from langchain_community.vectorstores import AzureSearch

# 1. Wczytywanie zmiennych środowiskowych
cfg = Path(__file__).parent / "local.settings.json"
if cfg.exists():
    data = json.loads(cfg.read_text("utf-8")).get("Values", {})
    for k, v in data.items():
        os.environ.setdefault(k, v)

load_dotenv()

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

# 3. Wczytanie produktów
products_path = Path(__file__).parent / "ask_rag" / "products.json"
products = json.loads(products_path.read_text("utf-8"))

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

print("✅ Dokumenty zaindeksowane.")
