# app/voice/edge_tts.py
#
# Uses Microsoft Edge's online TTS service — free, no API key, no
# billing account. Unofficial (reverse-engineered), so it can break
# without notice, but is widely used and stable in practice.

import io

import av
import edge_tts


# ISO 639-1 (from the LLM's language_code) -> Edge neural voice.
LANGUAGE_TO_VOICE = {
    "en": "en-US-AvaNeural",
    "es": "es-ES-ElviraNeural",
    "de": "de-DE-KatjaNeural",
    "fr": "fr-FR-DeniseNeural",
    "pt": "pt-BR-FranciscaNeural",
    "it": "it-IT-ElsaNeural",
    "tr": "tr-TR-EmelNeural",
    "nl": "nl-NL-FennaNeural",
    "sv": "sv-SE-SofieNeural",
    "no": "nb-NO-PernilleNeural",
    "da": "da-DK-ChristelNeural",
    "fi": "fi-FI-NooraNeural",
    "hi": "hi-IN-SwaraNeural",
    "vi": "vi-VN-HoaiMyNeural",
    "ar": "ar-SA-ZariyahNeural",
    "he": "he-IL-HilaNeural",
    "ja": "ja-JP-NanamiNeural",
    "zh": "zh-CN-XiaoxiaoNeural",
}

DEFAULT_VOICE = "en-US-AvaNeural"


class EdgeTTS:
    async def synthesize(
        self,
        text: str,
        language_code: str = "en",
        sample_rate: int = 24000,
    ) -> bytes:
        if not text:
            return b""

        voice = LANGUAGE_TO_VOICE.get(
            language_code,
            DEFAULT_VOICE,
        )

        communicate = edge_tts.Communicate(text, voice)

        mp3_bytes = bytearray()

        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                mp3_bytes.extend(chunk["data"])

        return self._mp3_to_pcm16(
            bytes(mp3_bytes),
            sample_rate,
        )

    @staticmethod
    def _mp3_to_pcm16(
        mp3_bytes: bytes,
        sample_rate: int,
    ) -> bytes:
        if not mp3_bytes:
            return b""

        container = av.open(io.BytesIO(mp3_bytes))

        resampler = av.AudioResampler(
            format="s16",
            layout="mono",
            rate=sample_rate,
        )

        pcm = bytearray()

        for frame in container.decode(audio=0):
            for resampled_frame in resampler.resample(frame):
                pcm.extend(bytes(resampled_frame.planes[0]))

        container.close()

        return bytes(pcm)
