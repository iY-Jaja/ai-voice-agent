# AI Innovation

A bilingual first-line customer-support voice assistant built for the AssemblyAI Voice Agent Hackathon. AI Innovation helps Vietnamese- and English-speaking customers describe common issues, try safe troubleshooting, and prepare a concise handoff when a request needs a human. AssemblyAI Streaming Speech-to-Text transcribes browser microphone audio; Gemini streams replies; Edge TTS speaks them sentence-by-sentence. The app owns the orchestration, so transcription, language handling, response generation, and speech output can be changed independently.

## How it works

1. The browser captures microphone audio and sends mono PCM16 at 24 kHz over a WebSocket to FastAPI.
2. FastAPI streams audio to AssemblyAI's real-time Speech-to-Text API and forwards partial and final transcripts.
3. On each final turn, Gemini generates a response using conversation history and the detected language as a hint. An explicit language request takes precedence.
4. Edge TTS synthesizes completed sentences while Gemini is still generating. The server sends text events and PCM audio chunks back over the same WebSocket.
5. Speech-start events and the Interrupt button stop the current response and discard queued browser playback.

Recognition is currently configured for Vietnamese and English. Transcription latency depends on the network and service conditions; sub-second performance is a design goal, not a measured guarantee.

This is a support-workflow demo, not a live helpdesk integration: it has no company knowledge base, account/order lookup, ticket creation, or refund capability. The assistant is instructed not to invent policies or claim it completed account actions.

## Hackathon submission copy

**Title:** AI Innovation — Bilingual Voice Support

**Short description:** AI Innovation gives Vietnamese- and English-speaking customers a natural voice-first way to explain an issue, get safe initial troubleshooting, and prepare a clear handoff to human support.

**Technology tags:** AssemblyAI Streaming Speech-to-Text, Gemini, Edge TTS, FastAPI, Vietnamese, English, customer support.

**Demo flow:** Start a session and describe a common issue in Vietnamese. Show the live partial transcript, spoken response, then switch to English in the next turn. Interrupt a reply to demonstrate barge-in. End with a request that needs account access to show the assistant being transparent and preparing a human-support handoff rather than inventing an account action.

The complete copy, cover graphic, five-slide presentation, narrated slide-explainer video, and optional live-demo recording script are in [`submission/`](./submission/).

## Requirements

- Python 3.11 or newer
- An AssemblyAI API key with Streaming Speech-to-Text access
- A Gemini API key
- A modern browser with microphone access (localhost or HTTPS)

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
cp .env.example .env
```

Set `ASSEMBLYAI_API_KEY` and `GEMINI_API_KEY` in `.env`. The sample rate and model defaults are also listed there; the browser and AssemblyAI sample rates must remain aligned at 24 kHz.

Start the server:

```bash
python -m uvicorn app.main:app --reload
```

Open <http://127.0.0.1:8000>, allow microphone access, and select **Start conversation**. Describe a support issue in Vietnamese or English; you can change languages during a session. Use **Interrupt** to stop a reply or **End** to close the session. The `/health` endpoint returns a basic server health check.

Docker Compose is also supported after creating `.env`:

```bash
docker compose up --build
```

## Deploy the public demo on Render

Push the repository to GitHub, then create a Blueprint in the [Render Dashboard](https://dashboard.render.com/) from the repository. Render reads [`render.yaml`](./render.yaml), builds the Docker image, and checks `/health`. Enter `ASSEMBLYAI_API_KEY` and `GEMINI_API_KEY` as secrets when prompted; never commit those values. After deployment, use the service's HTTPS URL for the hackathon submission. The Blueprint selects Render's free plan, which may spin down when idle; a paid plan may be needed for an always-on demo.

## Development

Run the test suite:

```bash
python -m pytest
```

## Privacy and service dependencies

Microphone audio and transcripts are sent to AssemblyAI for transcription. Conversation text is sent to Google Gemini for response generation. Reply text is sent to Microsoft's Edge TTS service for speech synthesis. Do not use the demo with sensitive or confidential information.
