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
source .venv/bin/activate