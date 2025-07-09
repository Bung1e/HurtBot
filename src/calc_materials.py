import json
import logging
import os
from pathlib import Path
from typing import Any

import pyodbc
from dotenv import load_dotenv
from langchain_azure_ai.chat_models import AzureAIChatCompletionsModel
from langchain_community.retrievers import AzureAISearchRetriever
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.output_parsers import JsonOutputParser
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


def determine_query_type(query: str) -> str:
    """
    'materials_calculation' lub 'general'
    """
    try:
        llm = AzureAIChatCompletionsModel(
            endpoint=os.getenv("AZURE_FOUNDRY_ENDPOINT"),
            credential=os.getenv("AZURE_FOUNDRY_KEY"),
            model=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT"),
            temperature=0.0,
        )

        classification_prompt = PromptTemplate.from_template(
            "Jesteś ekspertem w klasyfikacji zapytań klientów hurtowni budowlanej.\n"
            "Musisz określić typ zapytania i odpowiedzieć TYLKO jednym słowem.\n\n"
            "Zwróć TYLKO:\n"
            "materials_calculation - jeśli klient chce wiedzieć jakie materiały,\n"
            "ile potrzebuje do konkretnego zadania budowlanego\n"
            "general - wszystkie inne zapytania\n\n"
            "PRZYKŁADY materials_calculation:\n"
            "- Chcę wyremontować łazienkę 10m²\n"
            "- Ile potrzebuję materiałów do malowania pokoju?\n"
            "- Chcę zbudować taras 20m²\n"
            "- Potrzebuję materiałów na remont kuchni\n"
            "- Materiały do budowy tarasu 15m²\n\n"
            "PRZYKŁADY general:\n"
            "- Czy macie cement?\n"
            "- Ile kosztuje farba?\n"
            "- Jaki jest regulamin zwrotów?\n"
            "- Jakie macie płytki?\n\n"
            "Zapytanie klienta: '{query}'\n\n"
            "Odpowiedź (TYLKO jedno słowo):"
        )

        chain = classification_prompt | llm
        response = chain.invoke({"query": query})

        if hasattr(response, "content"):
            result = response.content.strip()
        else:
            result = str(response).strip()

        if "materials_calculation" in result:
            return "materials_calculation"
        else:
            return "general"

    except Exception as e:
        logger.error(f"Błąd podczas klasyfikacji zapytania: {e}")
        return "general"


def search_materials_info(query: str) -> str:
    try:
        search_query = f"materiały budowlane potrzebne do {query} lista ilość"
        search = DuckDuckGoSearchRun()
        search_results = search.run(search_query)
        logger.info(f"Wyniki wyszukiwania dla: {search_query}")
        return search_results
    except Exception as e:
        logger.error(f"Błąd podczas wyszukiwania: {e}")
        return "Nie udało się wyszukać informacji o materiałach."


def find_products_in_database(materials_list: list[str]) -> list[dict[str, Any]]:
    try:
        search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT") or ""
        search_service_name = search_endpoint.split("//")[-1].split(".")[0]
        search_api_key = os.getenv("AZURE_SEARCH_KEY") or ""

        products_retriever = AzureAISearchRetriever(
            content_key="content",
            index_name="products-index",
            top_k=5,
            service_name=search_service_name,
            api_key=search_api_key,
        )

        found_products = []

        for material in materials_list:
            try:
                docs = products_retriever.invoke(material)

                for doc in docs:
                    product_info = {
                        "content": doc.page_content,
                        "metadata": doc.metadata,
                        "search_term": material,
                    }
                    
                    product_id = doc.metadata.get("id")
                    if product_id:
                        sql_data = get_product_quantity_and_price(product_id)
                        if sql_data:
                            quantity, price = sql_data
                            product_info["current_quantity"] = quantity
                            product_info["current_price"] = price
                        else:
                            product_info["current_quantity"] = 0
                            product_info["current_price"] = None
                    else:
                        product_info["current_quantity"] = 0
                        product_info["current_price"] = None
                    
                    found_products.append(product_info)

            except Exception as e:
                logger.error(f"Błąd podczas wyszukiwania produktu {material}: {e}")

        return found_products

    except Exception as e:
        logger.error(f"Błąd podczas inicjalizacji retrievera: {e}")
        return []


def calculate_materials_cost(query: str) -> str:
    """
    kalkulacja materiałów
    """
    try:
        logger.info(f"Kalkulacja materiałów dla: {query}")

        search_results = search_materials_info(query)

        llm = AzureAIChatCompletionsModel(
            endpoint=os.getenv("AZURE_FOUNDRY_ENDPOINT") or "",
            credential=os.getenv("AZURE_FOUNDRY_KEY") or "",
            model=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT") or "",
            temperature=0.0,
        )

        analysis_prompt = PromptTemplate.from_template(
            "Na podstawie informacji z internetu, wyodrębnij materiały potrzebne do:"
            "{query}\n\n"
            "Informacje z internetu:\n{search_results}\n\n"
            "Podziel materiały na dwie kategorie:\n"
            "1. PODSTAWOWE - absolutnie niezbędne do wykonania zadania\n"
            "2. DODATKOWE - mogą być pomocne, ale nie są konieczne\n\n"
            "Zwróć JSON w formacie:\n"
            "{{\n"
            '  "basic_materials": [\n'
            '    {{"name": "nazwa", "quantity": "ilość", "unit": "jednostka"}}\n'
            "  ],\n"
            '  "additional_materials": [\n'
            '    {{"name": "nazwa", "quantity": "ilość", "unit": "jednostka"}}\n'
            "  ]\n"
            "}}"
        )

        parser = JsonOutputParser()
        analysis_chain = analysis_prompt | llm | parser
        materials_analysis = analysis_chain.invoke(
            {"query": query, "search_results": search_results}
        )

        basic_materials = materials_analysis.get("basic_materials", [])
        additional_materials = materials_analysis.get("additional_materials", [])

        basic_names = [m.get("name", "") for m in basic_materials]
        additional_names = [m.get("name", "") for m in additional_materials]

        basic_products = find_products_in_database(basic_names)
        additional_products = find_products_in_database(additional_names)

        result = "KALKULACJA MATERIAŁÓW\n\n"

        result += "MATERIAŁY PODSTAWOWE (niezbędne):\n"
        for material in basic_materials:
            material_name = material.get("name", "")
            quantity = material.get("quantity", "")
            unit = material.get("unit", "")

            result += f"• {material_name}: {quantity} {unit}\n"

            matching_products = [
                p for p in basic_products if material_name.lower() in p["content"].lower()
            ]

            if matching_products:
                result += "  Dostępne produkty:\n"
                for product in matching_products[:2]:  # max 2 produkty
                    name = product["metadata"].get("name", "Produkt")
                    
                    current_price = product.get("current_price")
                    current_quantity = product.get("current_quantity", 0)
                    
                    if current_price is not None:
                        availability = "✅ Dostępny" if current_quantity > 0 else "❌ Brak w magazynie"
                        result += f"    - {name}: {current_price} zł ({availability}, {current_quantity} szt.)\n"
                    else:
                        result += f"    - {name}: ❌ Brak danych o cenie i dostępności\n"
            else:
                result += "  ❌ Produkt niedostępny w naszej ofercie\n"

            result += "\n"

        if additional_materials:
            result += "MATERIAŁY DODATKOWE (mogą być pomocne):\n"
            for material in additional_materials:
                material_name = material.get("name", "")
                quantity = material.get("quantity", "")
                unit = material.get("unit", "")

                result += f"• {material_name}: {quantity} {unit}\n"

                matching_products = [
                    p
                    for p in additional_products
                    if material_name.lower() in p["content"].lower()
                ]

                if matching_products:
                    result += " Dostępne produkty:\n"
                    for product in matching_products[:2]:
                        name = product["metadata"].get("name", "Produkt")
                        
                        current_price = product.get("current_price")
                        current_quantity = product.get("current_quantity", 0)
                        
                        if current_price is not None:
                            availability = "✅ Dostępny" if current_quantity > 0 else "❌ Brak w magazynie"
                            result += f"    - {name}: {current_price} zł ({availability}, {current_quantity} szt.)\n"
                        else:
                            result += f"    - {name}: ❌ Brak danych o cenie i dostępności\n"
                else:
                    result += "  ❌ Produkt niedostępny w naszej ofercie\n"

                result += "\n"

        result += "Potrzebujesz dokładnej wyceny? Skontaktuj się z naszym doradcą!\n"
        result += "Ceny i dostępność sprawdzane w czasie rzeczywistym."

        return result

    except Exception as e:
        logger.error(f"Błąd podczas kalkulacji materiałów: {e}")
        return "Wystąpił błąd podczas kalkulacji materiałów. Spróbuj ponownie."


if __name__ == "__main__":
    test_query = "Chcę wyremontować łazienkę 10m²"
    result = determine_query_type(test_query)
    print(f"'{test_query}' - {result}")