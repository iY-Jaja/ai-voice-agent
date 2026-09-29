# app/voice/assemblyai_agent.py

import asyncio
import base64  # <-- ADD THIS
import json
from typing import Any, Awaitable, Callable

import websockets
from websockets.asyncio.client import ClientConnection

from app.config import settings


ASSEMBLYAI_VOICE_AGENT_URL = "wss://agents.assemblyai.com/v1/ws"


SUPPORTED_INPUT_LANGUAGES = [
    "vi",
    "en",
]


class AssemblyAIVoiceAgent:
    def __init__(
        self,
        on_event: Callable[
            [dict[str, Any]],
            Awaitable[None],
        ],
    ) -> None:
        self.on_event = on_event
        self.websocket: ClientConnection | None = None
        self.session_id: str | None = None
        self.receive_task: asyncio.Task[None] | None = None

    async def connect(self) -> None:
        self.websocket = await websockets.connect(
            ASSEMBLYAI_VOICE_AGENT_URL,
            additional_headers={
                "Authorization": (
                    f"Bearer {settings.assemblyai_api_key}"
                ),
            },
        )

        await self.send(
            {
                "type": "session.update",
                "session": {
                    "system_prompt": (
                        "You are a helpful realtime multilingual "
                        "voice assistant. "
                        "Understand the user's language and respond "
                        "naturally. "
                        "Keep responses concise and conversational. "
                        "The user may switch languages during a "
                        "conversation."
                    ),
                    # NOTE: AssemblyAI's built-in "greeting" field is
                    # deliberately omitted. Configuring it leaves this
                    # session unable to detect any speech after the
                    # greeting plays (verified: input.speech.started
                    # never fires again). The greeting is instead
                    # synthesized by VoiceSession itself once
                    # session.ready arrives.
                    "input": {
                        "language_codes": (
                            SUPPORTED_INPUT_LANGUAGES
                        ),
                        "transcription_mode": "min_latency",
                    },
                    "output": {
                        "voice": "alba",
                    },
                },
            }
        )

        self.receive_task = asyncio.create_task(
            self._receive_loop()
        )

    async def _receive_loop(self) -> None:
        if self.websocket is None:
            return

        try:
            async for raw_message in self.websocket:
                event = json.loads(raw_message)

                event_type = event.get("type")

                if event_type == "session.ready":
                    self.session_id = event.get(
                        "session_id"
                    )

                elif event_type == "session.ended":
                    self.session_id = None

                await self.on_event(event)

        except asyncio.CancelledError:
            raise

        except Exception as exc:
            await self.on_event(
                {
                    "type": "session.error",
                    "code": "connection_error",
                    "message": str(exc),
                }
            )

    async def send(
        self,
        event: dict[str, Any],
    ) -> None:
        if self.websocket is None:
            raise RuntimeError(
                "AssemblyAI session is not connected"
            )

        await self.websocket.send(
            json.dumps(event)
        )

    async def send_audio(
        self,
        pcm_audio: bytes,
    ) -> None:
        if not pcm_audio:
            return

        await self.send(
            {
                "type": "input.audio",
                "audio": base64.b64encode(
                    pcm_audio
                ).decode("ascii"),
            }
        )

    async def end(self) -> None:
        if self.websocket is None:
            return

        try:
            await self.send(
                {
                    "type": "session.end",
                }
            )
        except Exception:
            pass

        if self.receive_task is not None:
            self.receive_task.cancel()

            try:
                await self.receive_task
            except asyncio.CancelledError:
                pass

            self.receive_task = None

        await self.websocket.close()

        self.websocket = None
        self.session_id = None