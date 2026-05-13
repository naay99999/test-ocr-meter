# Digital Meter OCR API — Test Suite

Integration tests for the **Digital Meter OCR API v2.7.0** (`wayu199/meter-ocr:v4`).  
32 tests covering all 7 endpoints: file upload, image URL, async callback, and task polling.

## Prerequisites

- Python 3.10+
- Docker

---

## Quickstart

### 1. Clone and install

```bash
git clone <repo-url>
cd ocr-api-test

python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure `.env`

```bash
cp .env.example .env
```

Open `.env` and fill in the required values:

```env
API_KEY=your_api_key_here        # key used by the test suite (X-API-Key header)
BASE_URL=http://localhost:8080   # leave as-is if running Docker locally
```

> `PUBLIC_URL` is only needed for async callback tests — see [Callback Tests](#callback-tests) below.

### 3. Pull and start the API container

```bash
docker pull wayu199/meter-ocr:v4

docker run -d --name meter-ocr \
  -e OCR_API_KEY=$(grep '^API_KEY' .env | cut -d= -f2) \
  -p 8080:8080 \
  wayu199/meter-ocr:v4
```

Wait a few seconds for the models to load, then verify:

```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/docs
# → 200
```

### 4. Run tests

```bash
pytest tests/ -v
```

Expected output: **32 passed** in ~25 seconds (excluding callback wait time).

---

## Run Tests by Group

```bash
# File upload tests
pytest tests/test_upload.py -v

# Image URL tests
pytest tests/test_imageurl.py -v

# Async callback tests (requires tunnel — see below)
pytest tests/test_async_callback.py -v

# Task polling tests (requires tunnel — see below)
pytest tests/test_tasks.py -v

# Single test
pytest tests/test_imageurl.py::test_imageurl_single_success -v

# Auth tests only
pytest tests/ -v -k "401"

# Skip callback-dependent tests (no tunnel needed)
pytest tests/ -v -k "not callback_received and not completed_after"
```

---

## Callback Tests

Tests named `*_callback_received` and `*_completed_after_callback` require the local test server (port `CALLBACK_PORT`, default `3456`) to be **publicly reachable** — the OCR container POSTs results back to your machine when processing finishes.

### Option A — ngrok

```bash
ngrok http 3456
# → Forwarding: https://abc123.ngrok-free.app -> http://localhost:3456
```

### Option B — Cloudflare Tunnel (no account needed)

```bash
cloudflared tunnel --url http://localhost:3456
# → https://xxx-yyy-zzz.trycloudflare.com
```

Copy the tunnel URL into `.env`:

```env
PUBLIC_URL=https://abc123.ngrok-free.app
```

Then run the full suite. Callback tests wait up to **2 minutes** (`CALLBACK_WAIT`) for the container to process and POST back.

---

## Configuration

All values are set in `.env` (copy from `.env.example`):

| Variable | Required | Default | Description |
|---|---|---|---|
| `API_KEY` | ✅ | — | API key sent as `X-API-Key` header in every request |
| `BASE_URL` | | `http://localhost:8080` | URL of the OCR API server |
| `PUBLIC_URL` | callback tests only | — | Public tunnel URL for receiving callbacks |
| `CALLBACK_PORT` | | `3456` | Local port for the callback receiver server |
| `SYNC_TIMEOUT` | | `60` | Request timeout (s) for `/uploadimage`, `/imageurl` |
| `ASYNC_TIMEOUT` | | `30` | Request timeout (s) for `/async-callback`, `/tasks` |
| `CALLBACK_WAIT` | | `120` | Max wait (s) for OCR server to POST callback back |
| `IMAGE_PATH` | | `image/example.jpg` | Local image used for file upload tests |

---

## Endpoints Covered

| Endpoint | Method | Test File |
|---|---|---|
| `/uploadimage` | POST | `test_upload.py` |
| `/uploadimage/batch` | POST | `test_upload.py` |
| `/imageurl` | POST | `test_imageurl.py` |
| `/imageurl/batch` | POST | `test_imageurl.py` |
| `/async-callback/imageurl` | POST | `test_async_callback.py` |
| `/async-callback/imageurl/batch` | POST | `test_async_callback.py` |
| `/tasks/{task_id}` | GET | `test_tasks.py` |

---

## Cleanup

```bash
docker stop meter-ocr && docker rm meter-ocr
```
