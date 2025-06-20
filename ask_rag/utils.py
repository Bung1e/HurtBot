import os

from azure.core.credentials import AzureKeyCredential
from langchain.openai import OpenAIEmbeddings
from langchain.vectorstores import AzureSearch

# Inicjalizacja
emb = OpenAIEmbeddings(
    model="text-embedding-ada-002",
    openai_api_key=os.getenv("AZURE_OPENAI_KEY"),
    openai_api_base=os.getenv("AZURE_OPENAI_ENDPOINT"),
    openai_api_type="azure",
    openai_api_version="2023-07-01-preview",
)
vectorstore = AzureSearch(
    search_endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
    index_name="products-index",
    credential=AzureKeyCredential(os.getenv("AZURE_SEARCH_KEY")),
    embedding=emb,
    text_key="description",
    name_key="id",
)


def search_products(query: str) -> str:
    docs = vectorstore.similarity_search(query, k=3)
    if not docs:
        return "Brak dopasowań produktów."
    lines = []
    for d in docs:
        id_ = d.metadata["id"]
        nm = d.metadata.get("name")
        lines.append(f"{nm} ({id_}): {d.page_content}")
    return "Znalezione produkty:\n" + "\n".join(lines)
