import asyncio
from collections.abc import AsyncIterator

from google import genai
from google.genai import errors
from google.genai import types
from pydantic import BaseModel

from app.config import settings


class AgentReply(BaseModel):
    language_code: str
    text: str


class LLM:
    def __init__(self) -> None:
        self.client = genai.Client(
            api_key=settings.gemini_api_key
        )

        self.model = settings.gemini_model

    async def generate(
        self,
        messages: list[dict[str, str]],
    ) -> AgentReply:
        system_instruction = None
        contents: list[types.Content] = []

        for message in messages:
            if message["role"] == "system":
                system_instruction = message["content"]
                continue

            contents.append(
                types.Content(
                    role=(
                        "model"
                        if message["role"] == "assistant"
                        else "user"
                    ),
                    parts=[
                        types.Part.from_text(
                            text=message["content"]
                        )
                    ],
                )
            )

        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=AgentReply,
            ),
        )

        if isinstance(response.parsed, AgentReply):
            return response.parsed

        return AgentReply.model_validate_json(response.text)

    async def stream(
        self,
        messages: list[dict[str, str]],
    ) -> AsyncIterator[str]:
        system_instruction = None
        conversation = []

        for message in messages:
            if message["role"] == "system":
                system_instruction = message["content"]
                continue

            conversation.append(message)

        if not conversation or conversation[-1]["role"] != "user":
            raise ValueError(
                "Gemini streaming requires a latest user message"
            )

        history = [
            types.Content(
                role=(
                    "model"
                    if message["role"] == "assistant"
                    else "user"
                ),
                parts=[
                    types.Part.from_text(
                        text=message["content"]
                    )
                ],
            )
            for message in conversation[:-1]
        ]

        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            max_output_tokens=96,
            temperature=0.5,
        )

        for attempt in range(3):
            chat = self.client.aio.chats.create(
                model=self.model,
                history=history,
                config=config,
            )
            emitted_text = False

            try:
                stream = await chat.send_message_stream(
                    conversation[-1]["content"]
                )
                async for chunk in stream:
                    if chunk.text:
                        emitted_text = True
                        yield chunk.text
                return
            except errors.APIError as exc:
                if (
                    getattr(exc, "code", None) != 503
                    or emitted_text
                    or attempt == 2
                ):
                    raise

                await asyncio.sleep(0.5 * (attempt + 1))
