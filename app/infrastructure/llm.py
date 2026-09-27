from google import genai
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
