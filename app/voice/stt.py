from io import BytesIO

from openai import AsyncOpenAI

from app.config import settings


class SpeechToText:
    def __init__(self) -> None:
        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key
        )

        self.model = settings.openai_stt_model

    async def transcribe(
        self,
        audio: bytes,
        filename: str = "audio.webm",
    ) -> str:
        if not audio:
            return ""

        audio_file = BytesIO(audio)

        audio_file.name = filename

        response = await self.client.audio.transcriptions.create(
            model=self.model,
            file=audio_file,
        )

        return response.text.strip()
