import azure.functions as func
import json
from ask_rag import ask_rag

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        q = req.get_json().get("question", "")
    except:
        return func.HttpResponse("Zła struktura JSON", status_code=400)
    if not q:
        return func.HttpResponse("Brak pytania", status_code=400)
    ans = ask_rag(q)
    return func.HttpResponse(json.dumps({"answer": ans}), mimetype="application/json")
