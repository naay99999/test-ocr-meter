# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## About

Integration tests for the **Digital Meter OCR API** (v2.6.8), which reads meter values from images using AI/OCR. Tests run against a live remote API at `https://wayuth-meter-ocr.hf.space`.

## Setup

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env with your API key
echo "API_KEY=your_api_key_here" > .env
```

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run a specific test file
pytest tests/test_upload.py -v
pytest tests/test_imageurl.py -v
pytest tests/test_async_callback.py -v
pytest tests/test_tasks.py -v

# Run a single test by name
pytest tests/test_imageurl.py::test_imageurl_single_success -v

# Run only auth tests
pytest tests/ -v -k "401"
```

> Tests that wait for async callbacks (`test_*_callback_received`, `test_get_task_completed_after_callback`) can take up to **2 minutes** — the Hugging Face Space server is slow to process and fire callbacks.

## Architecture

### Test Infrastructure (`conftest.py`)

`conftest.py` runs a **dual-purpose local FastAPI server** on port 3456 for the entire test session:

1. **Callback receiver** — `POST /callback` stores the incoming payload in `_callback_store` and sets `_callback_event` (a `threading.Event`). Async callback tests use the `callback_store` and `callback_event` fixtures to wait on and inspect the result.
2. **Static file server** — serves `image/example.jpg` at `/image/example.jpg` so the remote API can fetch it via a public URL.

The server is exposed publicly at `PUBLIC_URL = "https://worktree.naay.cc"` — this domain must be reachable from the internet for callback tests to work. `IMAGE_URL` and `CALLBACK_URL` are both constructed from this public URL.

### Key Constants (`conftest.py`)

| Constant | Value |
|---|---|
| `BASE_URL` | `https://wayuth-meter-ocr.hf.space` |
| `PUBLIC_URL` | `https://worktree.naay.cc` |
| `CALLBACK_PORT` | `3456` |

## API Overview

The API exposes three groups of endpoints:

### 1. File Upload (`/uploadimage`)
- `POST /uploadimage` — upload a single image file, get OCR result synchronously
- `POST /uploadimage/batch` — upload multiple image files, get array of results

### 2. Image URL (`/imageurl`)
- `POST /imageurl` — send an image URL, server downloads and processes it (recommended for mobile apps)
- `POST /imageurl/batch` — send multiple image URLs, get array of results

### 3. Async Callback (`/async-callback/imageurl`)
- `POST /async-callback/imageurl` — send image URL + callback URL; responds `accepted` immediately, then POSTs result to callback URL when done
- `POST /async-callback/imageurl/batch` — same for multiple images; callback receives array of results

### 4. Task Status (`/tasks`)
- `GET /tasks/{task_id}` — poll status of an async job (`processing` | `completed`)

## Key Request/Response Schemas

### `ImageUrlRequest`
```json
{
  "image_url": "https://example.com/meter.jpg",
  "overlay": { "overlay_top": 0, "overlay_left": 0, "overlay_width": 100, "overlay_height": 100 },
  "gauge_min": null,
  "gauge_max": null
}
```

### `MeterResponse` (current, v2.6.8)
```json
{
  "data": { "meterId": "12345", "value": 991.1 },
  "warnings": ["Col 2: Abnormal roll."]
}
```
- `warnings` is an array of strings (empty on clean reads)
- `data.value` is a **number** (not a string)
- `data.meterId` holds the meter ID

### `AsyncCallbackRequest`
Same as `ImageUrlRequest` plus a required `callback_url` field. The callback POST body:
```json
{
  "task_id": "550e8400-...",
  "results": { "data": { "meterId": "12345", "value": 991.1 }, "warnings": [] }
}
```

### Error types in `warnings`
| Code | Meaning |
|---|---|
| `"Target box not found."` | OBB couldn't locate meter frame |
| `"No digits found"` | OCR found no digits in detected box |
| `"Col X: Abnormal roll."` | Rolling digit detected at column X |
| `"Col X: Unclear stacked digits."` | Stacked digit ambiguous at column X |
| `"Col X: Too many digits (X)."` | Noisy detection (>3 stacked) at column X |
| `"ID Warning: Length is X (<=4)"` | Meter ID suspiciously short |
| `"Length Error: Elec expected 6, found X"` | Electricity meter digit count wrong |
| `"Length Error: Water expected 4 or 6, found X"` | Water meter digit count wrong |
| `"Length Error: Water_7 expected 7, found X"` | 7-digit water meter count wrong |

## Notes
- `overlay` crops the image before AI processing — improves speed and accuracy
- `gauge_min` / `gauge_max` are accepted but unused (legacy compatibility)
- Batch endpoints return results for all items even if some fail individually
- Auth is via `X-API-Key` header; missing or wrong key returns 401
