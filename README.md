# Digital Meter OCR API — Test Suite

Integration tests for the **Digital Meter OCR API v2.7.0** (`wayu199/meter-ocr:v4`).
Covers all 7 endpoints: file upload, image URL, async callback, and task polling.

## Prerequisites

- Python 3.10+
- Docker

## Setup

**1. Install dependencies**

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

**2. Pull the Docker image**

```bash
docker pull wayu199/meter-ocr:v4
```

**3. Create `.env`**

```
API_KEY=your_api_key_here
```

For async callback tests, also set your public tunnel URL (see [Callback Tests](#callback-tests)):

```
PUBLIC_URL=https://your-tunnel-url.example.com
```

**4. Start the API container**

```bash
docker run -d --name meter-ocr \
  -e OCR_API_KEY=$API_KEY \
  -p 8080:8080 \
  wayu199/meter-ocr:v4
```

> Replace `$API_KEY` with the value from your `.env` if your shell doesn't expand it automatically.

## Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run by endpoint group
pytest tests/test_upload.py -v
pytest tests/test_imageurl.py -v
pytest tests/test_async_callback.py -v
pytest tests/test_tasks.py -v

# Run a single test
pytest tests/test_imageurl.py::test_imageurl_single_success -v

# Run only auth tests
pytest tests/ -v -k "401"
```

## Callback Tests

Tests named `*_callback_received` and `*_completed_after_callback` require the local test server (port 3456) to be **publicly reachable** — the OCR container needs to POST results back to your machine.

**Set up a tunnel with ngrok or Cloudflare:**

```bash
# ngrok
ngrok http 3456

# Cloudflare Tunnel
cloudflared tunnel --url http://localhost:3456
```

Then add the tunnel URL to `.env`:

```
PUBLIC_URL=https://abc123.ngrok-free.app
```

**No tunnel? Skip these tests:**

```bash
pytest tests/ -v -k "not callback_received and not completed_after"
```

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

## Cleanup

```bash
docker stop meter-ocr && docker rm meter-ocr
```
