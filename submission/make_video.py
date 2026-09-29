#!/usr/bin/env python3
"""Build a narrated, slide-based project explainer using macOS speech and ffmpeg."""

from __future__ import annotations

import html
import shutil
import subprocess
import tempfile
import textwrap
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "ai-innovation-video.mp4"
WIDTH = 1600
HEIGHT = 900
FPS = 30

SCENES = [
    {
        "eyebrow": "ASSEMBLYAI VOICE AGENT HACKATHON · SEPTEMBER 2026",
        "title": ["Support,", "in your language."],
        "subtitle": [
            "AI Innovation · Vietnamese ↔ English",
            "A voice-first customer-support prototype",
        ],
        "cards": [
            ("VOICE-FIRST", "Speak naturally"),
            ("BILINGUAL", "Vietnamese + English"),
            ("HUMAN-AWARE", "Clear support handoff"),
        ],
        "voice": [
            (
                "Samantha",
                "Meet AI Innovation, a voice-first support assistant for Vietnamese and English speakers. It helps customers explain everyday problems and get clear first-step guidance.",
            )
        ],
    },
    {
        "eyebrow": "01 · THE CUSTOMER NEED",
        "title": ["Getting help", "should feel easier."],
        "subtitle": [
            "Language should not get in the way of a clear first response.",
        ],
        "cards": [
            ("LANGUAGE FRICTION", "Explain an issue in the language that feels natural."),
            ("FIRST STEPS", "Get concise, general troubleshooting guidance."),
            ("TRUST", "Know when the next step needs a real support person."),
        ],
        "voice": [
            (
                "Samantha",
                "Customer support can be harder when you have to explain a problem in another language. AI Innovation is designed to make that first conversation more natural, while keeping a human handoff in reach.",
            )
        ],
    },
    {
        "eyebrow": "02 · A VOICE-FIRST EXPERIENCE",
        "title": ["Speak. See.", "Switch. Interrupt."],
        "subtitle": [
            "A sample customer utterance — not a recording of a live session:",
        ],
        "quote": "“Đơn hàng của tôi chưa tới. Tôi nên làm gì?”",
        "cards": [
            ("LIVE TRANSCRIPT", "Follow partial and final recognition."),
            ("LANGUAGE CHOICE", "Continue in Vietnamese or English."),
            ("CUSTOMER CONTROL", "Interrupt a spoken response at any time."),
        ],
        "voice": [
            (
                "Samantha",
                "A customer can start in Vietnamese. For example:",
            ),
            ("Linh", "Đơn hàng của tôi chưa tới. Tôi nên làm gì?"),
            (
                "Samantha",
                "The assistant is designed to follow a language switch and let the customer interrupt at any point.",
            ),
        ],
    },
    {
        "eyebrow": "03 · BUILT ON ASSEMBLYAI",
        "title": ["Real-time speech in.", "Orchestrated support out."],
        "subtitle": [
            "The application controls how the speech and response layers work together.",
        ],
        "cards": [
            ("ASSEMBLYAI", "Streaming Speech-to-Text over WebSocket."),
            ("FASTAPI + GEMINI", "Conversation orchestration and streamed replies."),
            ("EDGE TTS", "Sentence-sized spoken audio returned to the browser."),
        ],
        "voice": [
            (
                "Samantha",
                "AssemblyAI Streaming Speech-to-Text handles live audio transcription. FastAPI coordinates each turn. Gemini generates the reply, and Edge TTS returns spoken sentences. The app controls how these parts work together.",
            )
        ],
    },
    {
        "eyebrow": "04 · RESPONSIBLE SUPPORT",
        "title": ["Helpful, without", "pretending to be the helpdesk."],
        "subtitle": [
            "A prototype for safe initial guidance — not account operations.",
        ],
        "cards": [
            ("IT CAN", "Offer concise general troubleshooting and a support summary."),
            ("IT CANNOT", "Access accounts, check orders, issue refunds, or create tickets."),
            ("NEXT STEP", "Direct account-specific requests to official human support."),
        ],
        "voice": [
            (
                "Samantha",
                "This is a prototype, not a connected helpdesk. It cannot check accounts or orders, issue refunds, or create tickets. It avoids pretending, and points account-specific requests to official support. AI Innovation: support, in your language.",
            )
        ],
    },
]


def require_tool(name: str) -> str:
    tool = shutil.which(name)
    if not tool:
        raise RuntimeError(f"Required tool not found on PATH: {name}")
    return tool


def svg_text(lines: list[str], x: int, y: int, size: int, color: str, weight: int = 400) -> str:
    return "".join(
        f'<text x="{x}" y="{y + index * int(size * 1.2)}" fill="{color}" '
        f'font-family="Arial, sans-serif" font-size="{size}" font-weight="{weight}">'
        f'{html.escape(line)}</text>'
        for index, line in enumerate(lines)
    )


def scene_svg(scene: dict[str, object], index: int) -> str:
    title = scene["title"]
    subtitle = scene["subtitle"]
    cards = scene["cards"]
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="900" viewBox="0 0 1600 900">',
        '<defs><linearGradient id="bg" x2="1" y2="1"><stop stop-color="#291642"/><stop offset=".55" stop-color="#32184e"/><stop offset="1" stop-color="#17102d"/></linearGradient><pattern id="grid" width="48" height="48" patternUnits="userSpaceOnUse"><path d="M48 0H0V48" fill="none" stroke="#efe0ff" stroke-opacity=".045"/></pattern></defs>',
        '<rect width="1600" height="900" fill="url(#bg)"/><rect width="1600" height="900" fill="url(#grid)"/>',
        '<circle cx="1370" cy="215" r="250" fill="#91f5d5" opacity=".035"/>',
        f'<text x="100" y="92" fill="#91f5d5" font-family="Arial, sans-serif" font-size="19" letter-spacing="3">{html.escape(str(scene["eyebrow"]))}</text>',
        svg_text(title, 96, 225, 76, "#fbf8ff", 700),
        svg_text(subtitle, 102, 410, 28, "#cbbfda"),
    ]

    if "quote" in scene:
        parts.extend(
            [
                '<rect x="100" y="475" width="1400" height="86" rx="18" fill="#91f5d5" fill-opacity=".09" stroke="#91f5d5" stroke-opacity=".45"/>',
                f'<text x="135" y="530" fill="#91f5d5" font-family="Arial, sans-serif" font-size="34">{html.escape(str(scene["quote"]))}</text>',
            ]
        )

    cards = list(cards)
    if len(cards) == 3:
        positions = [(100, 575), (585, 575), (1070, 575)]
        card_width = 430
        card_height = 150
    else:
        positions = [(100, 590), (585, 590), (1070, 590)]
        card_width = 430
        card_height = 142

    for position, card in zip(positions, cards):
        x, y = position
        label, detail = card
        detail_lines = textwrap.wrap(detail, width=36)
        parts.extend(
            [
                f'<rect x="{x}" y="{y}" width="{card_width}" height="{card_height}" rx="16" fill="#ffffff" fill-opacity=".035" stroke="#e8d8ff" stroke-opacity=".22"/>',
                f'<text x="{x + 22}" y="{y + 38}" fill="#91f5d5" font-family="Arial, sans-serif" font-size="16" font-weight="700" letter-spacing="1">{html.escape(label)}</text>',
                svg_text(detail_lines[:3], x + 22, y + 76, 19, "#cbbfda"),
            ]
        )

    progress_width = int(1400 * index / len(SCENES))
    parts.extend(
        [
            '<line x1="100" y1="815" x2="1500" y2="815" stroke="#e8d8ff" stroke-opacity=".25"/>',
            f'<line x1="100" y1="815" x2="{100 + progress_width}" y2="815" stroke="#91f5d5" stroke-width="4"/>',
            '<text x="100" y="852" fill="#cbbfda" font-family="Arial, sans-serif" font-size="15" letter-spacing="2">AI INNOVATION  /  BILINGUAL VOICE SUPPORT</text>',
            f'<text x="1410" y="852" fill="#cbbfda" font-family="Arial, sans-serif" font-size="15">{index:02d} / {len(SCENES):02d}</text>',
            "</svg>",
        ]
    )
    return "".join(parts)


def run(command: list[str]) -> None:
    subprocess.run(command, check=True, stdout=subprocess.DEVNULL)


def main() -> None:
    ffmpeg = require_tool("ffmpeg")
    ffprobe = require_tool("ffprobe")
    say = require_tool("say")
    sips = require_tool("sips")

    with tempfile.TemporaryDirectory(prefix="ai-innovation-video-") as temp_name:
        temp = Path(temp_name)
        clip_paths: list[Path] = []

        for index, scene in enumerate(SCENES, start=1):
            scene_svg_path = temp / f"scene-{index:02d}.svg"
            scene_png_path = temp / f"scene-{index:02d}.png"
            scene_svg_path.write_text(scene_svg(scene, index))
            run([sips, "-s", "format", "png", str(scene_svg_path), "--out", str(scene_png_path)])

            wav_paths: list[Path] = []
            for voice_index, (voice, narration) in enumerate(scene["voice"]):
                audio_file = temp / f"scene-{index:02d}-voice-{voice_index:02d}.aiff"
                wav_file = temp / f"scene-{index:02d}-voice-{voice_index:02d}.wav"
                run([say, "-v", voice, "-r", "158", "-o", str(audio_file), narration])
                run([ffmpeg, "-y", "-i", str(audio_file), "-ar", "48000", "-ac", "2", str(wav_file)])
                wav_paths.append(wav_file)

            narration_wav = temp / f"scene-{index:02d}.wav"
            if len(wav_paths) == 1:
                shutil.copyfile(wav_paths[0], narration_wav)
            else:
                inputs: list[str] = []
                filter_inputs = "".join(f"[{i}:a]" for i in range(len(wav_paths)))
                for wav_path in wav_paths:
                    inputs.extend(["-i", str(wav_path)])
                run(
                    [
                        ffmpeg,
                        "-y",
                        *inputs,
                        "-filter_complex",
                        f"{filter_inputs}concat=n={len(wav_paths)}:v=0:a=1[a]",
                        "-map",
                        "[a]",
                        str(narration_wav),
                    ]
                )

            probe = subprocess.run(
                [
                    ffprobe,
                    "-v",
                    "error",
                    "-show_entries",
                    "format=duration",
                    "-of",
                    "default=noprint_wrappers=1:nokey=1",
                    str(narration_wav),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            duration = float(probe.stdout.strip()) + 1.2
            clip_path = temp / f"clip-{index:02d}.mp4"
            run(
                [
                    ffmpeg,
                    "-y",
                    "-loop",
                    "1",
                    "-framerate",
                    str(FPS),
                    "-i",
                    str(scene_png_path),
                    "-i",
                    str(narration_wav),
                    "-vf",
                    f"scale=1280:720,fade=t=in:st=0:d=0.35,fade=t=out:st={duration - 0.4:.3f}:d=0.35,format=yuv420p",
                    "-af",
                    f"apad,atrim=0:{duration:.3f},afade=t=out:st={duration - 0.4:.3f}:d=0.35",
                    "-t",
                    f"{duration:.3f}",
                    "-r",
                    str(FPS),
                    "-c:v",
                    "libx264",
                    "-preset",
                    "medium",
                    "-crf",
                    "22",
                    "-c:a",
                    "aac",
                    "-b:a",
                    "128k",
                    "-shortest",
                    str(clip_path),
                ]
            )
            clip_paths.append(clip_path)

        concat_file = temp / "concat.txt"
        concat_file.write_text(
            "".join(f"file '{path.as_posix()}'\n" for path in clip_paths)
        )
        run(
            [
                ffmpeg,
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat_file),
                "-c",
                "copy",
                "-movflags",
                "+faststart",
                str(OUTPUT),
            ]
        )

    print(f"Created {OUTPUT}")


if __name__ == "__main__":
    main()
