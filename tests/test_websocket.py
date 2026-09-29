import asyncio
import json
import re
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

from assemblyai.streaming.v3 import TurnEvent
from fastapi.testclient import TestClient
from google.genai import errors

from app.agent.agent import Agent
from app.infrastructure.llm import LLM
from app.main import app
from app.voice.session import VoiceSession
from app.voice.assemblyai_stt import AssemblyAIStreamingSTT


client = TestClient(app)


def test_env_example_matches_browser_audio_sample_rate() -> None:
    project_root = Path(__file__).resolve().parents[1]
    environment: dict[str, str] = {}

    example_path = project_root / ".env.example"
    for line in example_path.read_text().splitlines():
        if not line or line.startswith("#"):
            continue

        key, value = line.split("=", maxsplit=1)
        assert key not in environment
        environment[key] = value

    browser_html = (project_root / "client" / "index.html").read_text()
    sample_rate = re.search(r"const SAMPLE_RATE = (\d+);", browser_html)

    assert sample_rate is not None
    assert environment["ASSEMBLYAI_SAMPLE_RATE"] == sample_rate.group(1)
    assert environment["ASSEMBLYAI_STT_MODEL"] == "universal-3-6-pro"
    assert environment["ASSEMBLYAI_API_KEY"] == "your_assemblyai_api_key"
    assert environment["GEMINI_API_KEY"] == "your_gemini_api_key"


def test_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
    }


def test_agent_stream_includes_support_guardrails_and_language_hint() -> None:
    async def run() -> None:
        class FakeLLM:
            messages: list[dict[str, str]] = []

            async def stream(self, messages: list[dict[str, str]]):
                self.messages = messages
                yield "I can help with that."

        fake_llm = FakeLLM()
        agent = Agent.__new__(Agent)
        agent.llm = fake_llm

        chunks = [
            chunk
            async for chunk in agent.stream(
                [{"role": "user", "content": "Where is my order?"}],
                "vi",
            )
        ]

        system_prompt = fake_llm.messages[0]["content"]
        assert chunks == ["I can help with that."]
        assert "Never invent company-specific policies" in system_prompt
        assert "The detected language code is vi" in system_prompt

    asyncio.run(run())


def test_streaming_stt_adapter_initializes() -> None:
    adapter = AssemblyAIStreamingSTT()

    assert adapter.connected is False


def test_stt_adapter_ignores_duplicate_final_turns() -> None:
    on_final = Mock()
    adapter = AssemblyAIStreamingSTT(on_final=on_final)
    event = TurnEvent.model_validate(
        {
            "type": "Turn",
            "turn_order": 2,
            "turn_is_formatted": True,
            "end_of_turn": True,
            "transcript": "Hello.",
            "end_of_turn_confidence": 1.0,
            "words": [],
            "language_code": "en",
        }
    )

    adapter._on_turn(None, event)
    adapter._on_turn(None, event)

    on_final.assert_called_once_with("Hello.", "en")


def test_sentence_split_keeps_incomplete_tail() -> None:
    sentences, tail = VoiceSession._split_complete_sentences(
        "First sentence. Second sentence"
    )

    assert sentences == ["First sentence."]
    assert tail == " Second sentence"


def test_explicit_language_preference_overrides_and_persists() -> None:
    session = VoiceSession.__new__(VoiceSession)
    session.preferred_language_code = None

    first_language = session._resolve_response_language(
        "Could you speak in English only?",
        "it",
    )
    next_language = session._resolve_response_language(
        "What is the weather?",
        "vi",
    )

    assert first_language == "en"
    assert next_language == "en"


def test_tts_forwards_each_sentence_audio_chunk() -> None:
    async def run() -> None:
        session = VoiceSession.__new__(VoiceSession)
        session.tts = AsyncMock()
        session.tts.synthesize.side_effect = [b"first pcm", b"second pcm"]
        session.websocket = AsyncMock()
        session.send_lock = asyncio.Lock()
        sentence_queue: asyncio.Queue[str | None] = asyncio.Queue()
        await sentence_queue.put("First sentence.")
        await sentence_queue.put("Second sentence.")
        await sentence_queue.put(None)

        await session._synthesize_queued_sentences(
            sentence_queue,
            "vi",
        )

        assert session.tts.synthesize.await_args_list[0].args == (
            "First sentence.",
        )
        assert session.tts.synthesize.await_args_list[0].kwargs == {
            "language_code": "vi",
        }
        assert session.websocket.send_bytes.await_args_list[0].args == (
            b"first pcm",
        )
        assert session.websocket.send_bytes.await_args_list[1].args == (
            b"second pcm",
        )

    asyncio.run(run())


def test_final_turn_streams_gemini_text_and_edge_audio() -> None:
    async def run() -> None:
        class FakeWebSocket:
            def __init__(self) -> None:
                self.events: list[tuple[str, object]] = []

            async def send_text(self, message: str) -> None:
                self.events.append(("text", json.loads(message)))

            async def send_bytes(self, audio: bytes) -> None:
                self.events.append(("audio", audio))

        class FakeAgent:
            async def stream(
                self,
                conversation: list[dict[str, str]],
                language_code: str | None,
            ):
                assert conversation[0]["content"] == "Xin chào"
                assert language_code == "vi"
                yield "Xin chào."
                yield " Bạn khỏe không?"

        class FakeTTS:
            def __init__(self) -> None:
                self.calls: list[tuple[str, str]] = []

            async def synthesize(
                self,
                text: str,
                language_code: str,
            ) -> bytes:
                self.calls.append((text, language_code))
                return text.encode("utf-8")

        session = VoiceSession.__new__(VoiceSession)
        session.websocket = FakeWebSocket()
        session.agent = FakeAgent()
        session.tts = FakeTTS()
        session.conversation = []
        session.send_lock = asyncio.Lock()
        session.response_task = None

        await session._respond("Xin chào", "vi")

        text_events = [
            payload
            for event_type, payload in session.websocket.events
            if event_type == "text"
        ]
        audio_events = [
            payload
            for event_type, payload in session.websocket.events
            if event_type == "audio"
        ]

        assert [event["type"] for event in text_events] == [
            "llm_started",
            "assistant_text_delta",
            "assistant_text_delta",
            "assistant_text",
            "reply_done",
        ]
        assert [text for text, _ in session.tts.calls] == [
            "Xin chào.",
            "Bạn khỏe không?",
        ]
        assert all(language == "vi" for _, language in session.tts.calls)
        assert len(audio_events) == 2
        assert session.conversation[-1] == {
            "role": "assistant",
            "content": "Xin chào. Bạn khỏe không?",
        }

    asyncio.run(run())


def test_gemini_stream_uses_chat_history_and_latest_user_turn() -> None:
    async def run() -> None:
        class FakeChat:
            def __init__(self) -> None:
                self.latest_message = ""

            async def send_message_stream(self, message: str):
                self.latest_message = message

                async def chunks():
                    yield SimpleNamespace(text="Hello")
                    yield SimpleNamespace(text=" there.")

                return chunks()

        class FakeChats:
            def __init__(self) -> None:
                self.chat = FakeChat()
                self.create_kwargs: dict[str, object] = {}

            def create(self, **kwargs: object) -> FakeChat:
                self.create_kwargs = kwargs
                return self.chat

        chats = FakeChats()
        llm = LLM.__new__(LLM)
        llm.model = "gemini-test"
        llm.client = SimpleNamespace(
            aio=SimpleNamespace(chats=chats)
        )
        messages = [
            {"role": "system", "content": "Be concise."},
            {"role": "user", "content": "Earlier question."},
            {"role": "assistant", "content": "Earlier answer."},
            {"role": "user", "content": "Latest question."},
        ]

        chunks = [chunk async for chunk in llm.stream(messages)]

        assert chunks == ["Hello", " there."]
        assert chats.create_kwargs["model"] == "gemini-test"
        assert chats.create_kwargs["config"].system_instruction == "Be concise."
        history = chats.create_kwargs["history"]
        assert [message.role for message in history] == ["user", "model"]
        assert chats.chat.latest_message == "Latest question."

    asyncio.run(run())


def test_gemini_stream_retries_transient_503_before_text() -> None:
    async def run() -> None:
        class FakeChat:
            def __init__(self, attempt: int) -> None:
                self.attempt = attempt

            async def send_message_stream(self, message: str):
                if self.attempt == 1:
                    raise errors.APIError(
                        503,
                        {
                            "error": {
                                "message": "Temporarily unavailable",
                                "status": "UNAVAILABLE",
                            },
                        },
                    )

                async def chunks():
                    yield SimpleNamespace(text="Recovered.")

                return chunks()

        class FakeChats:
            def __init__(self) -> None:
                self.attempts = 0

            def create(self, **kwargs: object) -> FakeChat:
                self.attempts += 1
                return FakeChat(self.attempts)

        chats = FakeChats()
        llm = LLM.__new__(LLM)
        llm.model = "gemini-test"
        llm.client = SimpleNamespace(
            aio=SimpleNamespace(chats=chats)
        )

        chunks = [
            chunk
            async for chunk in llm.stream(
                [
                    {"role": "system", "content": "Be concise."},
                    {"role": "user", "content": "Hello."},
                ]
            )
        ]

        assert chunks == ["Recovered."]
        assert chats.attempts == 2

    asyncio.run(run())


def test_session_speaks_fallback_when_gemini_remains_unavailable() -> None:
    async def run() -> None:
        class FakeWebSocket:
            def __init__(self) -> None:
                self.text_messages: list[dict[str, object]] = []
                self.audio_messages: list[bytes] = []

            async def send_text(self, message: str) -> None:
                self.text_messages.append(json.loads(message))

            async def send_bytes(self, audio: bytes) -> None:
                self.audio_messages.append(audio)

        class UnavailableAgent:
            async def stream(self, conversation, language_code):
                raise errors.APIError(
                    503,
                    {
                        "error": {
                            "message": "Temporarily unavailable",
                            "status": "UNAVAILABLE",
                        },
                    },
                )
                yield ""

        class FakeTTS:
            async def synthesize(
                self,
                text: str,
                language_code: str,
            ) -> bytes:
                assert language_code == "en"
                return b"fallback audio"

        session = VoiceSession.__new__(VoiceSession)
        session.websocket = FakeWebSocket()
        session.agent = UnavailableAgent()
        session.tts = FakeTTS()
        session.conversation = []
        session.send_lock = asyncio.Lock()
        session.response_task = None

        await session._respond("Hello", "en")

        assert session.websocket.text_messages[-2]["type"] == "assistant_text"
        assert session.websocket.text_messages[-1] == {
            "type": "reply_done",
            "status": "completed",
        }
        assert session.websocket.audio_messages == [b"fallback audio"]

    asyncio.run(run())