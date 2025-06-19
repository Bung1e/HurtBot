from azure.functions import HttpRequest, HttpResponse
from azure.functions.decorators import FunctionApp

from ask_rag import ask_rag
import json
import logging
import traceback

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
        query = body.get("question", "")
        if not query:
            logger.warning("Brak pytania w żądaniu.")
            return HttpResponse("Brak pytania", status_code=400)

        logger.info(f"Odebrano zapytanie: {query}")
        answer = ask_rag(query)

        return HttpResponse(
            json.dumps({"answer": answer}), status_code=200, mimetype="application/json"
        )
    except Exception:
        traceback_str = traceback.format_exc()
        logger.exception("Błąd podczas przetwarzania zapytania.")
        return HttpResponse(traceback_str, status_code=500)
