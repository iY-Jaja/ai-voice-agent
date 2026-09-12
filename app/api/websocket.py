# app/api/websocket.py

from fastapi import APIRouter, WebSocket

from app.voice.session import VoiceSession


router = APIRouter()


@router.websocket("/ws/voice")
async def voice_websocket(
    websocket: WebSocket,
) -> None:
    await websocket.accept()

    session = VoiceSession(
        websocket=websocket,
    )

    try:
        await session.receive_loop()

    except Exception as exc:
        print(
            f"WebSocket session "
            f"{session.session_id} failed: {exc}"
        )

    finally:
        print(
            f"WebSocket session "
            f"{session.session_id} closed"
        )