import json
import logging

from azure.functions import HttpRequest, HttpResponse
from azure.functions.decorators import FunctionApp

from src.ask_rag import ask_rag

# ——————————————————————
# 1. Konfiguracja logowania
# ——————————————————————
logging.basicConfig(
    level=logging.INFO, format="[%(asctime)s] [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# ——————————————————————
# 2. Azure Function App
# ——————————————————————
app = FunctionApp()


@app.function_name(name="ask_rag")
@app.route(route="ask_rag", methods=["POST"])
def ask_rag_func(req: HttpRequest) -> HttpResponse:
    try:
        body = req.get_json()
        query = body.get("question", "").strip()
        if not query:
            logger.warning("⚠️ Brak pytania w żądaniu.")
            return HttpResponse("Brak pytania", status_code=400)

        logger.info(f"📩 Zapytanie: {query}")
        answer = ask_rag(query)

        return HttpResponse(
            json.dumps({"answer": answer}), status_code=200, mimetype="application/json"
        )

    except Exception:
        logger.exception("❌ Błąd podczas obsługi zapytania.")
        return HttpResponse(
            "Wystąpił błąd serwera — nie udało się przetworzyć zapytania.",
            status_code=500,
        )
