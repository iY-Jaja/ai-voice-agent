# app/voice/session.py
#
# AssemblyAI's own reply.audio is discarded (no Vietnamese voice);
# the agent's text reply is instead synthesized via Edge TTS.

import json
import uuid
from typing import Any

from fastapi import WebSocket

from app.voice.assemblyai_agent import AssemblyAIVoiceAgent
from app.voice.edge_tts import EdgeTTS


GREETING_TEXT = "Xin chào, tôi có thể giúp gì cho bạn?"


class VoiceSession:
    def __init__(
        self,
        websocket: WebSocket,
    ) -> None:
        self.websocket = websocket
        self.session_id = str(uuid.uuid4())

        self.agent = AssemblyAIVoiceAgent(
            on_event=self._handle_agent_event,
        )

        self.tts = EdgeTTS()

    async def receive_loop(self) -> None:
        await self.agent.connect()

        try:
            while True:
                message = await self.websocket.receive()

                if message.get("type") == "websocket.disconnect":
                    break

                binary_data = message.get("bytes")

                if binary_data is not None:
                    await self.agent.send_audio(
                        binary_data
                    )
                    continue

                text_data = message.get("text")

                if text_data is not None:
                    await self._handle_client_event(
                        text_data
                    )

        finally:
            await self.agent.end()

    async def _handle_client_event(
        self,
        text_data: str,
    ) -> None:
        try:
            event = json.loads(text_data)
        except json.JSONDecodeError:
            await self._send_json(
                {
                    "type": "error",
                    "message": "Invalid JSON",
                }
            )
            return

        event_type = event.get("type")

        if event_type == "start":
            await self._send_json(
                {
                    "type": "session_started",
                    "session_id": self.session_id,
                }
            )
            return

        if event_type == "interrupt":
            await self._send_json(
                {
                    "type": "interrupted",
                }
            )
            return

        if event_type == "end":
            await self.agent.end()
            return

        await self._send_json(
            {
                "type": "error",
                "message": (
                    f"Unknown event type: {event_type}"
                ),
            }
        )

    async def _handle_agent_event(
        self,
        event: dict[str, Any],
    ) -> None:
        event_type = event.get("type")

        if event_type == "session.ready":
            await self._send_json(
                {
                    "type": "session_ready",
                    "session_id": event.get(
                        "session_id"
                    ),
                }
            )

            # TEMP DEBUG: greeting disabled to isolate the bug
            return

        if event_type == "session.updated":
            await self._send_json(
                {
                    "type": "assemblyai_event",
                    "event": event,
                }
            )
            return

        if event_type == "input.speech.started":
            await self._send_json(
                {
                    "type": "speech_started",
                }
            )
            return

        if event_type == "input.speech.stopped":
            await self._send_json(
                {
                    "type": "speech_stopped",
                }
            )
            return

        if event_type == "transcript.user.delta":
            await self._send_json(
                {
                    "type": "transcript_partial",
                    "text": event.get("text", ""),
                }
            )
            return

        if event_type == "transcript.user":
            await self._send_json(
                {
                    "type": "transcript",
                    "text": event.get("text", ""),
                }
            )
            return

        if event_type == "reply.started":
            await self._send_json(
                {
                    "type": "llm_started",
                    "reply_id": event.get(
                        "reply_id"
                    ),
                }
            )
            return

        if event_type == "reply.audio":
            # AssemblyAI's own TTS cannot speak Vietnamese; the
            # reply is instead synthesized via Google TTS below,
            # once the full text is known.
            return

        if event_type == "transcript.agent":
            text = event.get("text", "")

            await self._send_json(
                {
                    "type": "assistant_text",
                    "text": text,
                    "interrupted": event.get(
                        "interrupted",
                        False,
                    ),
                }
            )

            # This flow uses AssemblyAI's own bundled LLM, which
            # doesn't report a language_code, so default to
            # Vietnamese here (see the Gemini-based orchestrator
            # for real per-reply language detection).
            audio_bytes = await self.tts.synthesize(
                text,
                language_code="vi",
            )

            if audio_bytes:
                await self.websocket.send_bytes(
                    audio_bytes
                )

            return

        if event_type == "reply.done":
            await self._send_json(
                {
                    "type": "reply_done",
                    "status": event.get(
                        "status"
                    ),
                }
            )
            return

        if event_type == "session.ended":
            await self._send_json(
                {
                    "type": "session_ended",
                }
            )
            return

        if event_type == "session.error":
            await self._send_json(
                {
                    "type": "error",
                    "code": event.get(
                        "code"
                    ),
                    "message": event.get(
                        "message"
                    ),
                }
            )
            return

        await self._send_json(
            {
                "type": "assemblyai_event",
                "event": event,
            }
        )

    async def _send_json(
        self,
        data: dict[str, Any],
    ) -> None:
        await self.websocket.send_text(
            json.dumps(data)
        )