from openai import AsyncOpenAI

from app.config import settings


class LLM:
    def __init__(self) -> None:
        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key
        )

        self.model = settings.openai_model

    async def generate(
        self,
        messages: list[dict[str, str]],
    ) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
        )

        content = response.choices[0].message.content

        return content or ""
