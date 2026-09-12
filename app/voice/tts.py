from openai import AsyncOpenAI

from app.config import settings


class TextToSpeech:
    def __init__(self) -> None:
        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key
        )

        self.model = settings.openai_tts_model

        self.voice = settings.openai_tts_voice

    async def synthesize(
        self,
        text: str,
    ) -> bytes:
        if not text:
            return b""

        response = await self.client.audio.speech.create(
            model=self.model,
            voice=self.voice,
            input=text,
            response_format="wav",
        )

        return response.read()
