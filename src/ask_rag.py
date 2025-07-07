import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
import json
import logging
import os
import re
from typing import Any

import pyodbc
from dotenv import load_dotenv
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_azure_ai.chat_models import AzureAIChatCompletionsModel
from langchain_community.retrievers import AzureAISearchRetriever
from langchain_core.prompts import PromptTemplate

from src.calc_materials import calculate_materials_cost, determine_query_type

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

cfg = Path(__file__).parent.parent / "local.settings.json"
if cfg.exists():
    data = json.loads(cfg.read_text("utf-8")).get("Values", {})
    for k, v in data.items():
        os.environ.setdefault(k, v)

load_dotenv()

products_path = Path(__file__).parent.parent / "data" / "products.json"
products: list[dict[str, Any]] = json.loads(products_path.read_text("utf-8"))


def connect_sql():
    return pyodbc.connect(os.getenv("SQL_CONNECTION_STRING"))


def get_quantity_from_sql(product_id: str) -> int | None:
    try:
        conn = connect_sql()
        cursor = conn.cursor()
        cursor.execute("SELECT quantity FROM stock WHERE product_id = ?", product_id)
        row = cursor.fetchone()
        conn.close()
        return row.quantity if row else None
    except Exception as e:
        logger.warning(f"Błąd podczas sprawdzania dostępności: {e}")
        return None


def decrease_quantity_in_sql(product_id: str) -> int | None:
    try:
        conn = connect_sql()
        cursor = conn.cursor()
        cursor.execute("SELECT quantity FROM stock WHERE product_id = ?", product_id)
        row = cursor.fetchone()
        if row and row.quantity > 0:
            new_quantity = row.quantity - 1
            cursor.execute(
                "UPDATE stock SET quantity = ? WHERE product_id = ?",
                (new_quantity, product_id),
            )
            conn.commit()
            conn.close()
            return new_quantity
        conn.close()
        return 0
    except Exception as e:
        logger.warning(f"Błąd przy zmniejszaniu stanu magazynowego: {e}")
        return None


def increase_quantity_in_sql(product_id: str, amount: int) -> int | None:
    try:
        product_id = str(product_id)
        amount = int(amount)
        conn = connect_sql()
        cursor = conn.cursor()

        cursor.execute("SELECT quantity FROM stock WHERE product_id = ?", (product_id,))
        row = cursor.fetchone()

        if row:
            current_quantity = int(row.quantity)
            new_quantity = current_quantity + amount
            cursor.execute(
                "UPDATE stock SET quantity = ? WHERE product_id = ?",
                (new_quantity, product_id),
            )
        else:
            new_quantity = amount
            cursor.execute(
                "INSERT INTO stock (product_id, quantity) VALUES (?, ?)",
                (product_id, new_quantity),
            )

        conn.commit()
        conn.close()
        return new_quantity

    except Exception as e:
        logger.exception(f"Błąd przy dodawaniu do magazynu: {e}")
        return None


def find_alternatives_by_category(
    category: str, exclude_id: str | None = None, max_results: int = 3
) -> list[dict[str, Any]]:
    return [
        p for p in products if p.get("category") == category and p.get("id") != exclude_id
    ][:max_results]


def handle_product_query(query: str) -> str | None:
    lower_query = query.lower()

    for product in products:
        name = product["name"].lower()
        if name in lower_query:
            product_id = product["id"]

            if any(
                w in lower_query for w in ["dostarczono", "dodaj", "uzupełnij", "przyjęto"]
            ):
                amount_match = re.search(r"(\d+)(?:\s*(?:sztuk|sztuki|szt\.?))?", lower_query)
                if amount_match:
                    amount = int(amount_match.group(1))
                    new_quantity = increase_quantity_in_sql(product_id, amount)
                    return f"Dodano {amount} sztuk produktu '{product['name']}' do magazynu. Nowa ilość: {new_quantity}."
                else:
                    return f"Nie rozpoznano liczby sztuk do dodania dla produktu '{product['name']}'."

            if "ile masz" in lower_query or "ile sztuk" in lower_query:
                quantity = get_quantity_from_sql(product_id)
                if quantity is None:
                    return f"Nie mam informacji o produkcie '{product['name']}'."
                return f"W magazynie jest {quantity} sztuk produktu '{product['name']}'."

            if "dostępny" in lower_query or "na magazynie" in lower_query:
                quantity = get_quantity_from_sql(product_id)
                if quantity is None:
                    return f"Nie mam informacji o dostępności produktu '{product['name']}'."
                elif quantity > 0:
                    return f"Produkt '{product['name']}' jest dostępny - {quantity} sztuk."
                else:
                    return f"Produkt '{product['name']}' jest niedostępny (brak w magazynie)."

            if "kup" in lower_query or "zamów" in lower_query:
                quantity = get_quantity_from_sql(product_id)
                if quantity is None:
                    return f"Nie mam informacji o produkcie '{product['name']}'."
                elif quantity == 0:
                    return f"Produkt '{product['name']}' jest wyprzedany."
                else:
                    new_quantity = decrease_quantity_in_sql(product_id)
                    return f"Zamówiono produkt '{product['name']}'. Pozostało {new_quantity} sztuk."

    return None


def handle_general_query(query: str) -> str:
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

        docs1 = retriever1.invoke(query)
        docs2 = retriever2.invoke(query)
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

    except Exception as e:
        logger.error(f"Błąd podczas obsługi ogólnego zapytania: {e}")
        return "Wystąpił błąd podczas przetwarzania zapytania."


def ask_rag(query: str) -> str:
    try:
        logger.info(f"Przetwarzanie zapytania: {query}")

        product_response = handle_product_query(query)
        if product_response:
            return product_response

        query_type = determine_query_type(query)
        logger.info(f"Rozpoznany typ zapytania: {query_type}")

        if query_type == "materials_calculation":
            return calculate_materials_cost(query)

        return handle_general_query(query)

    except Exception:
        logger.exception("Błąd wewnętrzny w ask_rag()")
        return "Wystąpił błąd wewnętrzny podczas przetwarzania zapytania."


if __name__ == "__main__":
    q = input("Zapytaj o produkt lub regulamin: ")
    print("\nOdpowiedź:")
    print(ask_rag(q))
