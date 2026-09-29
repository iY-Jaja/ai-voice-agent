# Optional live-demo video script

The ready-to-upload [`ai-innovation-video.mp4`](./ai-innovation-video.mp4) is a narrated slide explainer with a clearly labeled illustrative Vietnamese customer utterance. It is not a recording of the live application. Use the script below only if you also record a real deployed-app walkthrough.

**Target length:** 75–90 seconds  
**Format:** Screen recording with a short voiceover. Record the deployed HTTPS app after confirming the API keys work. Keep the browser address bar visible briefly so the public demo URL is clear; never show environment files, API keys, or account dashboards.

## Before recording

- Open the deployed app and confirm the status shows it is ready.
- Use a quiet room, headphones, and a working microphone.
- Close unrelated tabs and hide notifications.
- Start with an empty transcript.
- Keep answers short; if a live service is slow or fails, pause and retake rather than implying an untested success.

## Shot list and narration

### 0:00–0:10 — Problem and product

**On screen:** AI Innovation landing page.

**Say:** “Hi, this is AI Innovation: a bilingual voice-support assistant for Vietnamese- and English-speaking customers. It helps with safe first steps and is clear when a person needs to take over.”

### 0:10–0:30 — Vietnamese conversation

**On screen:** Start the session, wait for Ready, then speak:

> “Đơn hàng của tôi chưa tới. Tôi nên làm gì?”

Show the partial transcript, final transcript, and spoken answer.

**Say:** “The browser streams live microphone audio to AssemblyAI Streaming Speech-to-Text. The transcript appears as I speak, and AI Innovation responds in Vietnamese.”

### 0:30–0:48 — Switch language and interrupt

**On screen:** Ask:

> “Can you explain that in English?”

After the response begins, say:

> “One more thing—”

Show that speech interrupts the reply, then let the new turn finish.

**Say:** “The assistant follows a language change, and I can barge in instead of waiting for the voice response to finish.”

### 0:48–1:08 — Show safe support boundary

**On screen:** Ask:

> “Can you check my refund status?”

Let the answer play. It should explain that it cannot access account or refund records and suggest contacting the service’s official support.

**Say:** “AI Innovation does not pretend to access orders or issue refunds. It gives a transparent next step and can help prepare a summary for a human support agent.”

### 1:08–1:20 — Architecture and close

**On screen:** Show the architecture slide or README architecture section.

**Say:** “AssemblyAI provides real-time speech recognition. FastAPI orchestrates the conversation with Gemini, and Edge TTS streams spoken sentences back. That is AI Innovation.”

## Retake checklist

- The deployed app URL is readable and the live conversation succeeds.
- The video shows both languages, a transcript, audio playback, and an interruption.
- The refund question gets an honest limitation—not a fabricated lookup.
- No API key, private customer data, or unsupported performance claim appears.
