# Realtime Voice Agent

Realtime voice agent built with FastAPI and AssemblyAI Voice Agent API.

## Architecture

Browser
    |
    | WebSocket
    v
FastAPI
    |
    | WebSocket
    v
AssemblyAI Voice Agent API

AssemblyAI provides:

- Speech-to-text
- LLM reasoning
- Text-to-speech
- Voice activity detection
- Turn detection
- Interruption / barge-in
- Tool calling

## Requirements

- Python 3.11+
- AssemblyAI API key
- Modern browser with microphone support

## Setup

Create a virtual environment:

```bash
python3.12 -m venv .venv
source .venv/bin/activate      # macOS/Linux
.venv\Scripts\activate         # Windows
```

Install dependencies:

```bash
pip install -e ".[dev]"
```

# Build voice AI agents on AssemblyAI

Build a voice agent using AssemblyAI's real-time voice AI technology. Choose the approach that fits your idea and how much of the voice stack you want to build yourself.

## CHOOSE YOUR PATH

### Voice Agent API

Build an end-to-end voice agent through a single connection, with AssemblyAI handling the core voice interaction stack.
Speech-to-text powered by Universal-3 Pro
LLM routing and voice output
Turn-taking and voice activity detection
JSON-Schema tool calling
Designed for fast, natural voice interactions

### Realtime Speech-to-Text API

Use AssemblyAI's real-time speech-to-text API as the foundation of your voice agent, while bringing your own orchestration.
Real-time speech-to-text over WebSocket
Sub-second transcription
Multilingual speech recognition
Bring your own LLM and text-to-speech
More control over your voice agent architecture