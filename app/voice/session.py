import asyncio
import json
import re
import uuid
from collections.abc import AsyncIterator
from typing import Any

from fastapi import WebSocket

from app.agent.agent import Agent
from app.voice.assemblyai_stt import AssemblyAIStreamingSTT
from app.voice.edge_tts import EdgeTTS


class VoiceSession:
    def __init__(
        self,
        websocket: WebSocket,
    ) -> None:
        self.websocket = websocket
        self.session_id = str(uuid.uuid4())
        self.agent = Agent()
        self.tts = EdgeTTS()
        self.conversation: list[dict[str, str]] = []
        self.preferred_language_code: str | None = None
        self.loop: asyncio.AbstractEventLoop | None = None
        self.stt_events: asyncio.Queue[dict[str, Any]] | None = None
        self.send_lock = asyncio.Lock()
        self.response_task: asyncio.Task[None] | None = None
        self.stt = AssemblyAIStreamingSTT(
            on_partial=self._queue_partial,
            on_final=self._queue_final,
            on_speech_started=self._queue_speech_started,
            on_error=self._queue_error,
        )

    async def receive_loop(self) -> None:
        self.loop = asyncio.get_running_loop()
        self.stt_events = asyncio.Queue()
        event_task: asyncio.Task[None] | None = None

        try:
            await self.stt.start()
            event_task = asyncio.create_task(
                self._process_stt_events()
            )
            await self._send_json(
                {
                    "type": "session_ready",
                    "session_id": self.session_id,
                }
            )

            while True:
                message = await self.websocket.receive()

                if message.get("type") == "websocket.disconnect":
                    break

                binary_data = message.get("bytes")

                if binary_data is not None:
                    await self.stt.send_audio(binary_data)
                    continue

                text_data = message.get("text")

                if text_data is not None:
                    keep_running = await self._handle_client_event(
                        text_data,
                    )
                    if not keep_running:
                        break

        except Exception as exc:
            await self._send_json(
                {
                    "type": "error",
                    "message": str(exc),
                }
            )
            raise

        finally:
            await self._cancel_response()
            await self.stt.stop()
            if event_task is not None:
                event_task.cancel()
                await asyncio.gather(
                    event_task,
                    return_exceptions=True,
                )

    async def _handle_client_event(
        self,
        text_data: str,
    ) -> bool:
        try:
            event = json.loads(text_data)
        except json.JSONDecodeError:
            await self._send_json(
                {
                    "type": "error",
                    "message": "Invalid JSON",
                }
            )
            return True

        event_type = event.get("type")

        if event_type == "start":
            await self._send_json(
                {
                    "type": "session_started",
                    "session_id": self.session_id,
                }
            )
            return True

        if event_type == "interrupt":
            await self._cancel_response()
            return True

        if event_type == "end":
            return False

        await self._send_json(
            {
                "type": "error",
                "message": (
                    f"Unknown event type: {event_type}"
                ),
            }
        )
        return True

    def _queue_stt_event(
        self,
        event: dict[str, Any],
    ) -> None:
        if self.loop is None or self.stt_events is None:
            return

        self.loop.call_soon_threadsafe(
            self.stt_events.put_nowait,
            event,
        )

    def _queue_partial(self, text: str) -> None:
        self._queue_stt_event(
            {
                "type": "partial",
                "text": text,
            }
        )

    def _queue_final(
        self,
        text: str,
        language_code: str | None,
    ) -> None:
        self._queue_stt_event(
            {
                "type": "final",
                "text": text,
                "language_code": language_code,
            }
        )

    def _queue_speech_started(self) -> None:
        self._queue_stt_event({"type": "speech_started"})

    def _queue_error(self, message: str) -> None:
        self._queue_stt_event(
            {
                "type": "error",
                "message": message,
            }
        )

    def _resolve_response_language(
        self,
        user_text: str,
        detected_language: str | None,
    ) -> str:
        self.preferred_language_code = (
            self._requested_language_code(user_text)
            or self.preferred_language_code
        )
        return (
            self.preferred_language_code
            or detected_language
            or "en"
        )

    async def _process_stt_events(self) -> None:
        if self.stt_events is None:
            return

        while True:
            event = await self.stt_events.get()
            event_type = event["type"]

            if event_type == "speech_started":
                await self._cancel_response()
                await self._send_json(
                    {
                        "type": "speech_started",
                    }
                )
            elif event_type == "partial":
                await self._send_json(
                    {
                        "type": "transcript_partial",
                        "text": event["text"],
                    }
                )
            elif event_type == "final":
                await self._cancel_response()
                response_language = self._resolve_response_language(
                    event["text"],
                    event.get("language_code"),
                )
                await self._send_json(
                    {
                        "type": "speech_stopped",
                    }
                )
                await self._send_json(
                    {
                        "type": "transcript",
                        "text": event["text"],
                    }
                )
                self.response_task = asyncio.create_task(
                    self._respond(
                        event["text"],
                        response_language,
                    )
                )
            elif event_type == "error":
                await self._send_json(
                    {
                        "type": "error",
                        "message": event["message"],
                    }
                )

    async def _respond(
        self,
        user_text: str,
        language_code: str | None,
    ) -> None:
        self.conversation.append(
            {
                "role": "user",
                "content": user_text,
            }
        )
        await self._send_json({"type": "llm_started"})

        sentence_queue: asyncio.Queue[str | None] = asyncio.Queue()
        speech_task = asyncio.create_task(
            self._synthesize_queued_sentences(
                sentence_queue,
                language_code or "en",
            )
        )
        response_text = ""
        buffered_text = ""

        try:
            async for chunk in self.agent.stream(
                self.conversation,
                language_code,
            ):
                response_text += chunk
                buffered_text += chunk
                await self._send_json(
                    {
                        "type": "assistant_text_delta",
                        "text": chunk,
                    }
                )

                sentences, buffered_text = (
                    self._split_complete_sentences(
                        buffered_text
                    )
                )
                for sentence in sentences:
                    await sentence_queue.put(sentence)

            if buffered_text.strip():
                await sentence_queue.put(buffered_text.strip())
            await sentence_queue.put(None)
            await speech_task

            response_text = response_text.strip()
            if response_text:
                self.conversation.append(
                    {
                        "role": "assistant",
                        "content": response_text,
                    }
                )
                await self._send_json(
                    {
                        "type": "assistant_text",
                        "text": response_text,
                    }
                )

            await self._send_json(
                {
                    "type": "reply_done",
                    "status": "completed",
                }
            )
        except asyncio.CancelledError:
            speech_task.cancel()
            await asyncio.gather(
                speech_task,
                return_exceptions=True,
            )
            response_text = response_text.strip()
            if response_text:
                await self._send_json(
                    {
                        "type": "assistant_text",
                        "text": response_text,
                        "interrupted": True,
                    }
                )
            await self._send_json(
                {
                    "type": "reply_done",
                    "status": "interrupted",
                }
            )
            raise
        except Exception as exc:
            speech_task.cancel()
            await asyncio.gather(
                speech_task,
                return_exceptions=True,
            )
            if getattr(exc, "code", None) == 503:
                fallback_text = self._unavailable_message(
                    language_code or "en"
                )
                self.conversation.append(
                    {
                        "role": "assistant",
                        "content": fallback_text,
                    }
                )
                await self._send_json(
                    {
                        "type": "assistant_text",
                        "text": fallback_text,
                    }
                )
                try:
                    audio = await self.tts.synthesize(
                        fallback_text,
                        language_code=language_code or "en",
                    )
                except Exception:
                    audio = b""
                if audio:
                    async with self.send_lock:
                        await self.websocket.send_bytes(audio)
                await self._send_json(
                    {
                        "type": "reply_done",
                        "status": "completed",
                    }
                )
                return

            await self._send_json(
                {
                    "type": "error",
                    "message": str(exc),
                }
            )
            await self._send_json(
                {
                    "type": "reply_done",
                    "status": "error",
                }
            )
        finally:
            if self.response_task is asyncio.current_task():
                self.response_task = None

    @staticmethod
    def _requested_language_code(text: str) -> str | None:
        normalized_text = text.casefold()
        language_names = {
            "english": "en",
            "vietnamese": "vi",
        }

        for language_name, language_code in language_names.items():
            patterns = (
                rf"\b{language_name}\s+only\b",
                rf"\bonly\s+{language_name}\b",
                rf"\b(?:speak|respond|reply|answer|talk|use)\b"
                rf".{{0,40}}\b{language_name}\b",
            )
            if any(
                re.search(pattern, normalized_text)
                for pattern in patterns
            ):
                return language_code

        return None

    @staticmethod
    def _unavailable_message(language_code: str) -> str:
        if language_code == "vi":
            return (
                "Mình đang gặp sự cố kết nối tạm thời. "
                "Bạn vui lòng thử lại sau ít phút nhé."
            )
        return (
            "I am temporarily unable to generate a reply. "
            "Please try again in a moment."
        )

    async def _synthesize_queued_sentences(
        self,
        sentence_queue: asyncio.Queue[str | None],
        language_code: str,
    ) -> None:
        while True:
            sentence = await sentence_queue.get()
            if sentence is None:
                return

            try:
                audio = await self.tts.synthesize(
                    sentence,
                    language_code=language_code,
                )
            except Exception as exc:
                await self._send_json(
                    {
                        "type": "error",
                        "message": f"Speech synthesis failed: {exc}",
                    }
                )
                continue

            if audio:
                async with self.send_lock:
                    await self.websocket.send_bytes(audio)

    @staticmethod
    def _split_complete_sentences(
        text: str,
    ) -> tuple[list[str], str]:
        sentences: list[str] = []
        start = 0

        for index, character in enumerate(text):
            if character not in ".!?。！？\n":
                continue
            if index + 1 < len(text) and not text[index + 1].isspace():
                continue

            sentence = text[start : index + 1].strip()
            if sentence:
                sentences.append(sentence)
            start = index + 1

        return sentences, text[start:]

    async def _cancel_response(self) -> None:
        task = self.response_task
        if task is None or task.done():
            return

        task.cancel()
        await asyncio.gather(
            task,
            return_exceptions=True,
        )

    async def _send_json(
        self,
        data: dict[str, Any],
    ) -> None:
        async with self.send_lock:
            await self.websocket.send_text(json.dumps(data))