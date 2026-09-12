# app/main.py

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from app.api.websocket import router as websocket_router


BASE_DIR = Path(__file__).resolve().parent.parent
CLIENT_DIR = BASE_DIR / "client"


app = FastAPI(
    title="Realtime Multilingual Voice Agent",
    version="0.2.0",
)

app.include_router(websocket_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(
        CLIENT_DIR / "index.html"
    )