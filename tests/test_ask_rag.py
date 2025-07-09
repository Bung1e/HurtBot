import os

import pytest
from deepeval import evaluate
from deepeval.metrics import AnswerRelevancyMetric
from deepeval.test_case import LLMTestCase
from langchain_openai import AzureChatOpenAI


class AzureOpenAIModel:
    def __init__(self, model):
        self.model = model

    def generate(self, prompt: str) -> str:
        return self.model.invoke(prompt).content

    async def a_generate(self, prompt: str) -> str:
        return (await self.model.ainvoke(prompt)).content

    def get_model_name(self) -> str:
        return "AzureOpenAI_custom"


@pytest.mark.skipif(
    not os.getenv("AZURE_OPENAI_API_KEY")
    or not os.getenv("AZURE_OPENAI_ENDPOINT")
    or not os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT"),
    reason="Missing Azure OpenAI credentials in environment variables.",
)
def test_ask_rag_relevancy_eval() -> None:
    chat = AzureChatOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version="2023-05-15",
        azure_deployment=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    )
    azure_model = AzureOpenAIModel(chat)

    test_case = LLMTestCase(
        input="Czy macie farby akrylowe białe 10L?",
        expected_output="Tak, posiadamy",
    )
    metric = AnswerRelevancyMetric(model=azure_model)
    results = evaluate([test_case], [metric])
    min_acceptable_score = 0.7

    assert results[0].score >= min_acceptable_score, (
        f"Odpowiedź była zbyt słabo związana z kontekstem (score={results[0].score})"
    )
