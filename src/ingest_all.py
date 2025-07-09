import json
import os
import uuid
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_community.vectorstores import AzureSearch
from langchain_openai import AzureOpenAIEmbeddings
from pydantic import SecretStr

cfg = Path(__file__).parent.parent / "local.settings.json"
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

emb = AzureOpenAIEmbeddings(
    azure_deployment=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT") or "",
    model=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT") or "",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT") or "",
    api_key=SecretStr(os.getenv("AZURE_OPENAI_KEY") or ""),
    api_version="2023-07-01-preview",
)

products_path = Path(__file__).parent.parent / "data" / "products.json"
products: list[dict[str, Any]] = json.loads(products_path.read_text("utf-8"))

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

print(f"Wczytano {len(prod_docs)} produktów")

pdf_path = Path(__file__).parent.parent / "docs" / "REGULAMIN.pdf"
loader = PyMuPDFLoader(str(pdf_path))
pdf_docs = loader.load()

splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=150,
    separators=[
        "\n## ",
        "\n### ",
        "\n#### ",
        "\n\n",
        "\n",
        ". ",
        " ",
    ],
)

pdf_docs_to_upload = []
for doc in pdf_docs:
    chunks = splitter.split_text(doc.page_content)
    for chunk in chunks:
        embedding = emb.embed_documents([chunk])[0]
        pdf_docs_to_upload.append(
            {
                "id": f"pdf_{uuid.uuid4()}",
                "filename": "REGULAMIN.pdf",
                "content": chunk,
                "embedding": embedding,
            }
        )

print(f"Wczytano {len(pdf_docs_to_upload)} fragmentów PDF")

azure_products = AzureSearch(
    azure_search_endpoint=os.getenv("AZURE_SEARCH_ENDPOINT") or "",
    azure_search_key=os.getenv("AZURE_SEARCH_KEY") or "",
    index_name="products-index",
    embedding_function=emb,
    text_key="content",
    vector_field_name="embedding",
    document_id_key="id",
)

azure_regulamin = AzureSearch(
    azure_search_endpoint=os.getenv("AZURE_SEARCH_ENDPOINT") or "",
    azure_search_key=os.getenv("AZURE_SEARCH_KEY") or "",
    index_name="regulamin-index",
    embedding_function=emb,
    text_key="content",
    vector_field_name="embedding",
    document_id_key="id",
)

azure_products.client.upload_documents(prod_docs)
azure_regulamin.client.upload_documents(pdf_docs_to_upload)

print("Dokumenty zaindeksowane.")
