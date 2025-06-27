# ask_rag.py

import json
import logging
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_azure_ai.chat_models import AzureAIChatCompletionsModel
from langchain_community.retrievers import AzureAISearchRetriever
from langchain_core.prompts import PromptTemplate

# 1. Logowanie
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# 2. Wczytaj środowisko
cfg = Path(__file__).parent / "local.settings.json"
if cfg.exists():
    data = json.loads(cfg.read_text("utf-8")).get("Values", {})
    for k, v in data.items():
        os.environ.setdefault(k, v)

load_dotenv()

# 3. Wczytaj dane produktów
products_path = Path(__file__).parent / "products.json"
products: list[dict[str, Any]] = json.loads(products_path.read_text("utf-8"))


def find_alternatives_by_category(
    category: str,
    exclude_id: str | None = None,
    max_results: int = 3,
) -> list[dict[str, Any]]:
    candidates = [
        p
        for p in products
        if p.get("category") == category and p.get("id") != exclude_id
    ]
    return candidates[:max_results]


def safe_invoke(retriever: Any, query: str) -> list[Any]:
    """Safely invoke retriever and filter out documents with invalid content."""
    try:
        docs = retriever.invoke(query)
        valid_docs = []
        for doc in docs:
            if isinstance(doc.page_content, str) and doc.page_content.strip():
                valid_docs.append(doc)
            else:
                logger.warning(
                    "Filtered out document with invalid content: %r | %r",
                    doc.page_content,
                    doc.metadata,
                )
        return valid_docs
    except Exception as e:
        logger.error(f"Error invoking retriever: {e}")
        return []


# 4. Główna funkcja RAG
def ask_rag(query: str) -> str:
    try:
        logger.info(f"Zapytanie: {query}")

        search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT") or ""
        search_service_name = search_endpoint.split("//")[-1].split(".")[0]
        search_api_key = os.getenv("AZURE_SEARCH_KEY") or ""

        retriever1 = AzureAISearchRetriever(
            content_key="content",
            index_name="products-index",
            top_k=3,
            service_name=search_service_name,
            api_key=search_api_key,
        )

        retriever2 = AzureAISearchRetriever(
            content_key="content",
            index_name="regulamin-index",
            top_k=3,
            service_name=search_service_name,
            api_key=search_api_key,
        )

        docs1 = safe_invoke(retriever1, query)
        docs2 = safe_invoke(retriever2, query)
        # docs1 = retriever1.invoke(query)
        # docs2 = retriever2.invoke(query)
        all_docs = docs1 + docs2

        logger.info(f"Liczba dokumentów znalezionych: {len(all_docs)}")

        if not all_docs:
            return "Nie znaleziono żadnych pasujących dokumentów."

        used_categories = [
            d.metadata.get("category") for d in docs1 if d.metadata.get("category")
        ]
        alternatives: list[dict[str, Any]] = []
        if used_categories:
            primary_doc = docs1[0]
            alternatives = find_alternatives_by_category(
                category=str(used_categories[0]),
                exclude_id=str(primary_doc.metadata.get("id", "")),
            )

        llm = AzureAIChatCompletionsModel(
            endpoint=os.getenv("AZURE_FOUNDRY_ENDPOINT") or "",
            credential=os.getenv("AZURE_FOUNDRY_KEY") or "",
            model=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT") or "",
            temperature=0.0,
        )

        prompt = PromptTemplate.from_template(
            "Jesteś inteligentnym asystentem klienta hurtowni B2B.\n"
            "Odpowiadaj wyłącznie na podstawie poniższych dokumentów:\n\n"
            "{context}\n\nPytanie: {input}\nOdpowiedź:"
        )

        chain = create_stuff_documents_chain(llm=llm, prompt=prompt)
        response = chain.invoke({"input": query, "context": all_docs})

        if alternatives:
            alt_text = "\n\nAlternatywne produkty w tej samej kategorii:\n"
            for alt in alternatives:
                alt_text += f"- {alt.get('name')} — {alt.get('description')}\n"
            response += alt_text

        return str(response)

    except Exception:
        logger.exception("Błąd wewnętrzny w ask_rag()")
        return "Wystąpił błąd wewnętrzny podczas przetwarzania zapytania."


# 5. Test lokalny
if __name__ == "__main__":
    q = input("Zapytaj o produkt lub regulamin: ")
    print("\nOdpowiedź:")
    print(ask_rag(q))
