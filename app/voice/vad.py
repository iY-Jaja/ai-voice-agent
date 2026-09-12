class VoiceActivityDetector:
    """
    Placeholder for voice activity detection.

    V1 uses explicit audio_start/audio_end events.

    V2 will use VAD to automatically detect:
        speech started
        speech ended
    """

    def is_speech(
        self,
        audio_chunk: bytes,
    ) -> bool:
        return True

    def is_end_of_turn(self) -> bool:
        return False
