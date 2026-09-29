# Hackathon submission copy

## Basic information

**Project title**  
AI Innovation — Bilingual Voice Support

**Short description**  
AI Innovation helps Vietnamese- and English-speaking customers explain a support issue by voice, get safe initial troubleshooting, and prepare a clear handoff to human support.

**Long description**  
AI Innovation is a real-time, voice-first customer-support assistant for Vietnamese- and English-speaking customers. Speak naturally, follow the live transcript, and hear concise guidance in your preferred language. The assistant can be interrupted mid-response, and it is designed to be honest when a request needs a person.

AssemblyAI Streaming Speech-to-Text transcribes browser microphone audio over WebSocket. A FastAPI service orchestrates the session, Gemini streams conversational replies using the conversation history and detected language as a hint, and Edge TTS returns sentence-sized spoken audio. This modular design gives the application control over turn handling, language preference, response generation, and speech output.

AI Innovation is a prototype, not a connected helpdesk: it cannot access accounts or orders, check refund status, apply company policies, or create tickets. It provides general initial guidance and suggests an official human-support channel when account-specific help is needed. Recognition is currently configured for Vietnamese and English; transcription latency depends on network and service conditions.

## Technology and category tags

**Technology:** AssemblyAI Streaming Speech-to-Text, Gemini, Edge TTS, FastAPI, WebSocket  
**Language:** Vietnamese, English  
**Category:** Customer Support, Voice AI, Productivity

## Presentation assets

- Cover image: [`cover.png`](./cover.png)
- Slide presentation: [`ai-innovation-slides.pdf`](./ai-innovation-slides.pdf) (editable/presentable source: [`slides.html`](./slides.html)).
- Narrated slide-explainer video: [`ai-innovation-video.mp4`](./ai-innovation-video.mp4). This is a generated presentation, not a live app recording.
- Optional live-demo recording script: [`video-script.md`](./video-script.md)
- Video generator: [`make_video.py`](./make_video.py)

## Submission links

Fill these with the actual public links after deployment; do not submit the placeholders.

- Public GitHub repository: **[paste repository URL]**
- Deployed application: **[paste Render HTTPS URL]**
- Video presentation: upload `ai-innovation-video.mp4` or paste its hosted URL.
- Slide presentation: the PDF is ready to upload; add its hosted link here only if the platform requires one.
