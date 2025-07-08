import json
import logging
import os
import re
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))
from typing import Any

import pyodbc
from dotenv import load_dotenv
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_azure_ai.chat_models import AzureAIChatCompletionsModel
from langchain_community.retrievers import AzureAISearchRetriever
from langchain_core.prompts import PromptTemplate

import difflib
from langchain_core.documents import Document

from src.calc_materials import calculate_materials_cost, determine_query_type

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

load_dotenv()

cfg = Path(__file__).parent.parent / "local.settings.json"
if cfg.exists():
    data = json.loads(cfg.read_text("utf-8")).get("Values", {})
    for k, v in data.items():
        os.environ.setdefault(k, v)

products_path = Path(__file__).parent.parent / "data" / "products.json"
products: list[dict[str, Any]] = json.loads(products_path.read_text("utf-8"))


def connect_sql():
    return pyodbc.connect(os.getenv("SQL_CONNECTION_STRING"))


def get_product_quantity_and_price(product_id: str) -> tuple[int, float] | None:
    try:
        conn = connect_sql()
        cursor = conn.cursor()
        cursor.execute("SELECT quantity, price FROM stock WHERE product_id = ?", product_id)
        row = cursor.fetchone()
        conn.close()
        return (row.quantity, row.price) if row else None
    except Exception as e:
        logger.warning(f"SQL Error: {e}")
        return None


def find_alternatives_by_category(
    category: str, exclude_id: str | None = None, max_results: int = 3
) -> list[dict[str, Any]]:
    return [
        p for p in products if p.get("category") == category and p.get("id") != exclude_id
    ][:max_results]


def handle_general_query(query: str) -> str:
    try:
        logger.info(f"General query: {query}")
        search_service_name = os.getenv("AZURE_SEARCH_ENDPOINT").split("//")[-1].split(".")[0]
        search_api_key = os.getenv("AZURE_SEARCH_KEY")

        retriever_products = AzureAISearchRetriever(
            content_key="content",
            index_name="products-index",
            top_k=3,
            service_name=search_service_name,
            api_key=search_api_key,
        )
        retriever_regulamin = AzureAISearchRetriever(
            content_key="content",
            index_name="regulamin-index",
            top_k=3,
            service_name=search_service_name,
            api_key=search_api_key,
        )

        docs_products = retriever_products.invoke(query)
        docs_regulamin = retriever_regulamin.invoke(query)
        all_docs = docs_products + docs_regulamin

        if not all_docs:
            return "Brak informacji w bazie wiedzy."

        product_names = {p["name"]: p["id"] for p in products}
        best_matches = difflib.get_close_matches(query, product_names.keys(), n=1, cutoff=0.5)

        product_details = []
        if best_matches:
            matched_name = best_matches[0]
            matched_id = product_names[matched_name]

            sql_data = get_product_quantity_and_price(matched_id)
            if sql_data:
                quantity, price = sql_data
                product_details.append(
                    f"Produkt '{matched_name}': Ilość: {quantity}, Cena: {price} zł"
                )

        enriched_docs = all_docs.copy()
        if product_details:
            sql_info_doc = Document(
                page_content="\n".join(product_details),
                metadata={"source": "sql", "type": "product_data"}
            )
            enriched_docs.append(sql_info_doc)

        llm = AzureAIChatCompletionsModel(
            endpoint=os.getenv("AZURE_FOUNDRY_ENDPOINT"),
            credential=os.getenv("AZURE_FOUNDRY_KEY"),
            model=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT"),
            temperature=0.0,
        )

        prompt = PromptTemplate.from_template(
            "Jesteś asystentem klienta hurtowni B2B. Odpowiedz na podstawie poniższych dokumentów:\n\n"
            "{context}\n\nPytanie: {input}\nOdpowiedź:"
        )

        chain = create_stuff_documents_chain(llm=llm, prompt=prompt)
        response = chain.invoke({"input": query, "context": enriched_docs})

        return response

    except Exception as e:
        logger.error(f"Błąd w handle_general_query: {e}")
        return "Wystąpił błąd przetwarzania zapytania."



def ask_rag(query: str) -> str:
    try:
        logger.info(f"Zapytanie użytkownika: {query}")
        query_type = determine_query_type(query)
        logger.info(f"Typ zapytania: {query_type}")

        if query_type == "materials_calculation":
            return calculate_materials_cost(query)

        return handle_general_query(query)

    except Exception:
        logger.exception("Wewnętrzny błąd ask_rag")
        return "Błąd podczas przetwarzania zapytania."


if __name__ == "__main__":
    user_query = input("Zadaj pytanie: ")
    print(ask_rag(user_query))
