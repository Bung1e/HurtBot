import json

# Wczytaj dane z pliku lub zmiennej
with open("products.json", "r", encoding="utf-8") as f:
    full_data = json.load(f)

# Lista produktów
products = full_data["products"]

# Przygotowanie danych do indeksowania
search_documents = []

for product in products:
    doc = {
        "id": product["id"],
        "name": product["name"],
        "description": product.get("description", ""),
        "content": " ".join(
            [
                product.get("name", ""),
                product.get("description", ""),
                product.get("subcategory", ""),
                product.get("brand", ""),
                " ".join(product.get("certifications", [])),
                *[str(v) for v in product.get("technical_specs", {}).values()],
            ]
        ),
        # Jeśli chcesz dodać embedding później, zostaw miejsce:
        # "embedding": [0.0] * 1536
    }
    search_documents.append(doc)

# Zapisz jako gotowy do uploadu plik
with open("azure_search_docs.json", "w", encoding="utf-8") as f:
    json.dump(search_documents, f, ensure_ascii=False, indent=2)

print("✅ Zapisano plik 'azure_search_docs.json' zgodny z products-index")
