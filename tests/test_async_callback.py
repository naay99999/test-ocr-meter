"""Tests for POST /async-callback/imageurl and /async-callback/imageurl/batch"""

import time

import httpx
import pytest

from conftest import ASYNC_TIMEOUT as TIMEOUT, BASE_URL, CALLBACK_URL, CALLBACK_WAIT, HEADERS, IMAGE_URL


# ─── /async-callback/imageurl ─────────────────────────────────────────────────


def test_async_single_accepted(callback_store, callback_event):
    """ส่ง request → ต้องได้ status=accepted และ task_id ทันที"""
    payload = {"image_url": IMAGE_URL, "callback_url": CALLBACK_URL}
    response = httpx.post(
        f"{BASE_URL}/async-callback/imageurl", json=payload, headers=HEADERS, timeout=TIMEOUT
    )
    assert response.status_code in (200, 202), response.text
    data = response.json()
    assert data.get("status") == "accepted", f"unexpected status: {data}"
    assert "task_id" in data, "missing task_id"
    assert isinstance(data["task_id"], str)
    assert len(data["task_id"]) > 0


def test_async_single_callback_received(callback_store, callback_event):
    """รอรับ callback จาก OCR server → ต้องมี task_id และ results"""
    payload = {"image_url": IMAGE_URL, "callback_url": CALLBACK_URL}
    response = httpx.post(
        f"{BASE_URL}/async-callback/imageurl", json=payload, headers=HEADERS, timeout=TIMEOUT
    )
    task_id = response.json()["task_id"]

    deadline = time.time() + CALLBACK_WAIT
    while time.time() < deadline:
        callback_event.wait(timeout=min(10, deadline - time.time()))
        if callback_store.get("task_id") == task_id:
            break
        callback_event.clear()
    assert callback_store.get("task_id") == task_id, f"ไม่ได้รับ callback สำหรับ task {task_id} ภายใน {CALLBACK_WAIT}s"

    results = callback_store["results"]
    assert "data" in results
    assert "warnings" in results


def test_async_missing_callback_url():
    """ไม่ส่ง callback_url → 422"""
    payload = {"image_url": IMAGE_URL}
    response = httpx.post(
        f"{BASE_URL}/async-callback/imageurl", json=payload, headers=HEADERS, timeout=TIMEOUT
    )
    assert response.status_code == 422


def test_async_missing_image_url():
    """ไม่ส่ง image_url → 422"""
    payload = {"callback_url": CALLBACK_URL}
    response = httpx.post(
        f"{BASE_URL}/async-callback/imageurl", json=payload, headers=HEADERS, timeout=TIMEOUT
    )
    assert response.status_code == 422


def test_async_no_api_key_returns_401():
    """ไม่ส่ง X-API-Key → 401 Unauthorized"""
    payload = {"image_url": IMAGE_URL, "callback_url": CALLBACK_URL}
    response = httpx.post(
        f"{BASE_URL}/async-callback/imageurl", json=payload, timeout=TIMEOUT
    )
    assert response.status_code == 401, response.text


def test_async_wrong_api_key_returns_401():
    """ส่ง X-API-Key ผิด → 401 Unauthorized"""
    payload = {"image_url": IMAGE_URL, "callback_url": CALLBACK_URL}
    response = httpx.post(
        f"{BASE_URL}/async-callback/imageurl",
        json=payload,
        headers={"X-API-Key": "wrong-key"},
        timeout=TIMEOUT,
    )
    assert response.status_code == 401, response.text


# ─── /async-callback/imageurl/batch ──────────────────────────────────────────


def test_async_batch_accepted(callback_store, callback_event):
    """ส่ง batch 2 items → ต้องได้ status=accepted และ task_id"""
    payloads = [
        {"image_url": IMAGE_URL, "callback_url": CALLBACK_URL},
        {"image_url": IMAGE_URL, "callback_url": CALLBACK_URL},
    ]
    response = httpx.post(
        f"{BASE_URL}/async-callback/imageurl/batch", json=payloads, headers=HEADERS, timeout=TIMEOUT
    )
    assert response.status_code in (200, 202), response.text
    data = response.json()
    assert data.get("status") == "accepted", f"unexpected status: {data}"
    assert "task_id" in data


def test_async_batch_callback_received(callback_store, callback_event):
    """รอรับ callback จาก batch → results ต้องเป็น array"""
    payloads = [
        {"image_url": IMAGE_URL, "callback_url": CALLBACK_URL},
        {"image_url": IMAGE_URL, "callback_url": CALLBACK_URL},
    ]
    response = httpx.post(
        f"{BASE_URL}/async-callback/imageurl/batch", json=payloads, headers=HEADERS, timeout=TIMEOUT
    )
    task_id = response.json()["task_id"]

    deadline = time.time() + CALLBACK_WAIT
    while time.time() < deadline:
        callback_event.wait(timeout=min(10, deadline - time.time()))
        if callback_store.get("task_id") == task_id:
            break
        callback_event.clear()
    assert callback_store.get("task_id") == task_id, f"ไม่ได้รับ callback สำหรับ task {task_id} ภายใน {CALLBACK_WAIT}s"

    results = callback_store["results"]
    assert isinstance(results, list), f"results ต้องเป็น array แต่ได้: {type(results)}"
    assert len(results) == 2


def test_async_batch_missing_callback_url():
    """batch ที่ไม่มี callback_url → 422"""
    payloads = [{"image_url": IMAGE_URL}]
    response = httpx.post(
        f"{BASE_URL}/async-callback/imageurl/batch", json=payloads, headers=HEADERS, timeout=TIMEOUT
    )
    assert response.status_code == 422
