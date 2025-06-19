import json

import azure.functions as func

from ask_rag import ask_rag


def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        q = req.get_json().get("question", "")
    except Exception:
        return func.HttpResponse("Zła struktura JSON", status_code=400)
    if not q:
        return func.HttpResponse("Brak pytania", status_code=400)

    answer = ask_rag(q)
    return func.HttpResponse(json.dumps({"answer": answer}))
