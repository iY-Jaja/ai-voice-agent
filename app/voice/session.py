# app/voice/session.py
#
# IMPORTANT:
# reply.audio is a STREAM of PCM16 chunks.
# Do not treat each chunk as a complete audio file.

import base64
import json
import uuid
from typing import Any

from fastapi import WebSocket

from app.voice.assemblyai_agent import AssemblyAIVoiceAgent


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
            audio_data = event.get("data")

            if not audio_data:
                return

            audio_bytes = base64.b64decode(
                audio_data
            )

            await self.websocket.send_bytes(
                audio_bytes
            )

            return

        if event_type == "transcript.agent":
            await self._send_json(
                {
                    "type": "assistant_text",
                    "text": event.get(
                        "text",
                        "",
                    ),
                    "interrupted": event.get(
                        "interrupted",
                        False,
                    ),
                }
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