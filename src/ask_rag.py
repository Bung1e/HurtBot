import json
import logging
import os
import re
from pathlib import Path
from typing import Any

import pyodbc
from dotenv import load_dotenv
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_azure_ai.chat_models import AzureAIChatCompletionsModel
from langchain_community.retrievers import AzureAISearchRetriever
from langchain_core.prompts import PromptTemplate

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
    candidates = [
        p for p in products if p.get("category") == category and p.get("id") != exclude_id
    ]
    return candidates[:max_results]


def ask_rag(query: str) -> str:
    try:
        logger.info(f"Zapytanie: {query}")
        lower_query = query.lower()

        response_parts = []

        for product in products:
            name = product["name"].lower()
            if name in lower_query:
                product_id = product["id"]
                product_name = product["name"]

                if any(w in lower_query for w in ["dostarczono", "dodaj", "uzupełnij", "przyjęto"]):
                    match = re.search(r"(\d+)(?:\s*(?:sztuk|sztuki|szt\.?))?", lower_query)
                    if match:
                        amount = int(match.group(1))
                        new_qty = increase_quantity_in_sql(product_id, amount)
                        return (
                            f"Dodano {amount} sztuk produktu '{product_name}' "
                            f"do magazynu. Nowa ilość: {new_qty}."
                        )
                    return (
                        f"Nie rozpoznano liczby sztuk do dodania dla produktu '{product_name}'."
                    )

                if "dostępny" in lower_query or "na magazynie" in lower_query:
                    qty = get_quantity_from_sql(product_id)
                    if qty is None:
                        return f"Nie mam informacji o dostępności produktu '{product_name}'."
                    if qty > 0:
                        return f"Produkt '{product_name}' jest dostępny - {qty} sztuk."
                    return f"Produkt '{product_name}' jest niedostępny (brak w magazynie)."

                if "kup" in lower_query or "zamów" in lower_query:
                    qty = get_quantity_from_sql(product_id)
                    if qty is None:
                        return f"Nie mam informacji o produkcie '{product_name}'."
                    if qty == 0:
                        return f"Produkt '{product_name}' jest wyprzedany."
                    new_qty = decrease_quantity_in_sql(product_id)
                    return (
                        f"Zamówiono produkt '{product_name}'. "
                        f"Pozostało {new_qty} sztuk."
                    )

        # --- retrieval fallback ---

        search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT") or ""
        search_service = search_endpoint.split("//")[-1].split(".")[0]
        search_key = os.getenv("AZURE_SEARCH_KEY") or ""

        retriever1 = AzureAISearchRetriever(
            content_key="content",
            index_name="products-index",
            top_k=3,
            service_name=search_service,
            api_key=search_key,
        )
        retriever2 = AzureAISearchRetriever(
            content_key="content",
            index_name="regulamin-index",
            top_k=3,
            service_name=search_service,
            api_key=search_key,
        )

        docs = retriever1.invoke(query) + retriever2.invoke(query)
        logger.info(f"Liczba dokumentów znalezionych: {len(docs)}")

        if not docs:
            return "Nie znaleziono żadnych pasujących dokumentów."

        categories = [d.metadata.get("category") for d in docs if d.metadata.get("category")]
        alternatives = []
        if categories:
            alt_category = categories[0]
            primary_doc = docs[0]
            alternatives = find_alternatives_by_category(
                category=str(alt_category),
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
        answer = chain.invoke({"input": query, "context": docs})

        if alternatives:
            alt_text = "\n\nAlternatywne produkty w tej samej kategorii:\n"
            for alt in alternatives:
                alt_text += f"- {alt.get('name')} — {alt.get('description')}\n"
            answer += alt_text

        return str(answer)

    except Exception:
        logger.exception("Błąd wewnętrzny w ask_rag()")
        return "Wystąpił błąd wewnętrzny podczas przetwarzania zapytania."



if __name__ == "__main__":
    q = input("Zapytaj o produkt lub regulamin: ")
    print("\nOdpowiedź:")
    print(ask_rag(q))
