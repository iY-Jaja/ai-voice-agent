# app/voice/assemblyai_stt.py

import asyncio
from typing import Callable

from assemblyai.streaming.v3 import (
    RealTimeError,
    RealTimeEvents,
    RealTimeParameters,
    RealTimeTranscriber,
    RealTimeTranscriberOptions,
    SpeechStartedEvent,
    TurnEvent,
)

from app.config import settings


class AssemblyAIStreamingSTT:
    def __init__(
        self,
        on_partial: Callable[[str], None] | None = None,
        on_final: Callable[[str, str | None], None] | None = None,
        on_speech_started: Callable[[], None] | None = None,
        on_error: Callable[[str], None] | None = None,
    ) -> None:
        self.on_partial = on_partial
        self.on_final = on_final
        self.on_speech_started = on_speech_started
        self.on_error = on_error
        self.last_final_turn_order: int | None = None

        self.client = RealTimeTranscriber(
            RealTimeTranscriberOptions(
                connect_timeout=10.0,
            ),
            api_key=settings.assemblyai_api_key,
        )

        self.client.on(
            RealTimeEvents.Turn,
            self._on_turn,
        )
        self.client.on(
            RealTimeEvents.SpeechStarted,
            self._on_speech_started,
        )
        self.client.on(
            RealTimeEvents.Error,
            self._on_error,
        )

        self.connected = False

    def _on_turn(
        self,
        _: RealTimeTranscriber,
        event: TurnEvent,
    ) -> None:
        transcript = event.transcript.strip()

        if not transcript:
            return

        if event.end_of_turn:
            if (
                self.last_final_turn_order is not None
                and event.turn_order <= self.last_final_turn_order
            ):
                return

            self.last_final_turn_order = event.turn_order
            if self.on_final is not None:
                self.on_final(
                    transcript,
                    event.language_code,
                )
        else:
            if self.on_partial is not None:
                self.on_partial(transcript)

    def _on_speech_started(
        self,
        _: RealTimeTranscriber,
        __: SpeechStartedEvent,
    ) -> None:
        if self.on_speech_started is not None:
            self.on_speech_started()

    def _on_error(
        self,
        _: RealTimeTranscriber,
        error: RealTimeError,
    ) -> None:
        if self.on_error is not None:
            self.on_error(str(error))

    async def start(self) -> None:
        await asyncio.to_thread(
            self.client.connect,
            RealTimeParameters(
                sample_rate=settings.assemblyai_sample_rate,
                speech_model=settings.assemblyai_stt_model,
                language_codes=["vi", "en"],
                language_detection=True,
                min_turn_silence=150,
                max_turn_silence=700,
                include_partial_turns=True,
            ),
        )

        self.connected = True

    async def send_audio(
        self,
        audio: bytes,
    ) -> None:
        if not self.connected or not audio:
            return

        await asyncio.to_thread(
            self.client.stream,
            audio,
        )

    async def stop(self) -> None:
        if not self.connected:
            return

        self.connected = False

        await asyncio.to_thread(
            self.client.disconnect,
            terminate=True,
        )
