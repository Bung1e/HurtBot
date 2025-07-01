# mypy: disable-error-code=no-untyped-def

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

import os

from deepeval import evaluate
from deepeval.metrics import AnswerRelevancyMetric
from deepeval.models.base_model import DeepEvalBaseLLM
from deepeval.test_case import LLMTestCase
from langchain_openai import AzureChatOpenAI

from ask_rag import ask_rag


class AzureOpenAIModel(DeepEvalBaseLLM):
    def __init__(self, model):
        self.model = model

    def load_model(self):
        return self.model

    def generate(self, prompt: str) -> str:
        return self.model.invoke(prompt).content

    async def a_generate(self, prompt: str) -> str:
        return (await self.model.ainvoke(prompt)).content

    def get_model_name(self):
        return "AzureOpenAI_custom"


def test_ask_rag_relevancy_eval(): 
    chat = AzureChatOpenAI(
        openai_api_key=os.getenv("AZURE_OPENAI_KEY"),
        openai_api_version="2023-05-15",
        azure_deployment=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    )
    azure_model = AzureOpenAIModel(chat)

    question = "Czy mogę zwrócić produkt po 30 dniach?"
    answer = ask_rag(question)

    test_case = LLMTestCase(
        input=question,
        actual_output=answer,
        retrieval_context=[
            "Regulamin mówi, że produkt można zwrócić do 30 dni od zakupu."
        ],
    )

    metric = AnswerRelevancyMetric(threshold=0.7, model=azure_model)
    results = evaluate([test_case], [metric])

    min_acceptable_score = 0.7

    assert results[0].score >= min_acceptable_score, (
        f"Odpowiedź była zbyt słabo związana z kontekstem (score={results[0].score})"
    )
