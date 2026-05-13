import os
import threading
import time

import pytest
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles

load_dotenv()

# ─── Constants ────────────────────────────────────────────────────────────────

BASE_URL   = os.getenv("BASE_URL", "http://localhost:8080")
PUBLIC_URL = os.getenv("PUBLIC_URL", "https://worktree.naay.cc")
IMAGE_URL = f"{PUBLIC_URL}/image/example.jpg"
CALLBACK_URL = f"{PUBLIC_URL}/callback"
CALLBACK_PORT = int(os.getenv("CALLBACK_PORT",  "3456"))
IMAGE_PATH    = os.getenv("IMAGE_PATH",    "image/example.jpg")
SYNC_TIMEOUT  = int(os.getenv("SYNC_TIMEOUT",  "60"))
ASYNC_TIMEOUT = int(os.getenv("ASYNC_TIMEOUT", "30"))
CALLBACK_WAIT = int(os.getenv("CALLBACK_WAIT", "120"))

API_KEY = os.environ["API_KEY"]
HEADERS = {"X-API-Key": API_KEY}

# ─── Local callback/file server ───────────────────────────────────────────────

_callback_store: dict = {}
_callback_event = threading.Event()

_app = FastAPI()


@_app.post("/callback")
async def receive_callback(request: Request):
    data = await request.json()
    _callback_store.clear()
    _callback_store.update(data)
    _callback_event.set()
    return {"ok": True}


_app.mount("/image", StaticFiles(directory="image"), name="image")


@pytest.fixture(scope="session", autouse=True)
def local_server():
    """รัน FastAPI server ที่ port 3456 ตลอด session (serve image + รับ callback)"""
    config = uvicorn.Config(_app, host="0.0.0.0", port=CALLBACK_PORT, log_level="error")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    # รอให้ server พร้อม
    time.sleep(1.5)
    yield
    server.should_exit = True


@pytest.fixture
def callback_store():
    """Dict เก็บข้อมูล callback ล่าสุด — clear ก่อน test ทุกครั้ง"""
    _callback_store.clear()
    _callback_event.clear()
    return _callback_store


@pytest.fixture
def callback_event():
    """threading.Event ที่จะ set เมื่อได้รับ callback — clear ก่อน test ทุกครั้ง"""
    _callback_event.clear()
    return _callback_event
