# app/voice/assemblyai_stt.py

import asyncio
from typing import Callable

from assemblyai.streaming.v3 import (
    BeginEvent,
    RealTimeError,
    RealTimeEvents,
    RealTimeParameters,
    RealTimeTranscriber,
    RealTimeTranscriberOptions,
    TerminationEvent,
    TurnEvent,
)

from app.config import settings


class AssemblyAIStreamingSTT:
    def __init__(
        self,
        on_partial: Callable[[str], None] | None = None,
        on_final: Callable[[str], None] | None = None,
    ) -> None:
        self.on_partial = on_partial
        self.on_final = on_final

        self.client = RealTimeTranscriber(
            RealTimeTranscriberOptions(
                connect_timeout=10.0,
            ),
            api_key=settings.assemblyai_api_key,
        )

        self.client.on(
            RealTimeEvents.Begin,
            self._on_begin,
        )
        self.client.on(
            RealTimeEvents.Turn,
            self._on_turn,
        )
        self.client.on(
            RealTimeEvents.Termination,
            self._on_terminated,
        )
        self.client.on(
            RealTimeEvents.Error,
            self._on_error,
        )

        self.connected = False

    def _on_begin(
        self,
        _: RealTimeTranscriber,
        event: BeginEvent,
    ) -> None:
        print(f"AssemblyAI session started: {event.id}")

    def _on_turn(
        self,
        _: RealTimeTranscriber,
        event: TurnEvent,
    ) -> None:
        transcript = event.transcript.strip()

        if not transcript:
            return

        if event.end_of_turn:
            if self.on_final is not None:
                self.on_final(transcript)
        else:
            if self.on_partial is not None:
                self.on_partial(transcript)

    def _on_terminated(
        self,
        _: RealTimeTranscriber,
        event: TerminationEvent,
    ) -> None:
        print(
            "AssemblyAI session terminated: "
            f"{event.audio_duration_seconds}s"
        )

    def _on_error(
        self,
        _: RealTimeTranscriber,
        error: RealTimeError,
    ) -> None:
        print(f"AssemblyAI error: {error}")

    async def start(self) -> None:
        await asyncio.to_thread(
            self.client.connect,
            RealTimeParameters(
                sample_rate=settings.assemblyai_sample_rate,
                speech_model=settings.assemblyai_stt_model,
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
