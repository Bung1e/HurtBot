import os

import chainlit as cl
import requests

API_URL = os.getenv("API_URL", "http://localhost:7071/api/ask_rag")


@cl.on_chat_start
async def start():
    await cl.Message(
        content=("Hello! I'm HurtBot - your B2B assistant. Ask me about products or rules!")
    ).send()


@cl.on_message
async def main(message: cl.Message):
    async with cl.Step(name="Searching information") as step:
        step.input = message.content

        try:
            response = requests.post(
                API_URL,
                json={"question": message.content},
                headers={"Content-Type": "application/json"},
                timeout=30,
            )

            if response.ok:
                answer = response.json().get("answer", "")
                step.output = answer
            else:
                answer = f"api error: {response.status_code}"
                step.output = answer

        except Exception as e:
            answer = f"connection error: {e!s}"
            step.output = answer

    await cl.Message(content=answer).send()


@cl.on_settings_update
async def setup_agent(settings):
    print("settings updated:", settings)


@cl.set_chat_profiles
async def chat_profile():
    return [
        cl.ChatProfile(
            name="default",
            markdown_description="standard b2b consultant mode",
        ),
    ]


if __name__ == "__main__":
    pass
