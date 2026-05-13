"""Tests for GET /tasks/{task_id}"""

import time

import httpx

from conftest import ASYNC_TIMEOUT as TIMEOUT, BASE_URL, CALLBACK_URL, CALLBACK_WAIT, HEADERS, IMAGE_URL


# ─── /tasks/{task_id} ────────────────────────────────────────────────────────


def test_get_task_after_submit_returns_status():
    """submit async → ใช้ task_id ที่ได้ → GET /tasks/{id} → ต้องมี status field"""
    payload = {"image_url": IMAGE_URL, "callback_url": CALLBACK_URL}
    submit = httpx.post(
        f"{BASE_URL}/async-callback/imageurl", json=payload, headers=HEADERS, timeout=TIMEOUT
    )
    assert submit.status_code == 200, submit.text
    task_id = submit.json()["task_id"]

    time.sleep(1)  # v4 registers task asynchronously; brief wait avoids 404 race
    response = httpx.get(f"{BASE_URL}/tasks/{task_id}", headers=HEADERS, timeout=TIMEOUT)
    assert response.status_code == 200, response.text
    data = response.json()
    assert "status" in data, f"ต้องมี status field: {data}"
    assert data["status"] in ("processing", "completed", "callback_success", "callback_failed"), f"unexpected status: {data['status']}"


def test_get_task_completed_after_callback(callback_store, callback_event):
    """submit async → รอ callback → GET /tasks/{id} → status=completed และมี results"""
    payload = {"image_url": IMAGE_URL, "callback_url": CALLBACK_URL}
    submit = httpx.post(
        f"{BASE_URL}/async-callback/imageurl", json=payload, headers=HEADERS, timeout=TIMEOUT
    )
    assert submit.status_code == 200, submit.text
    task_id = submit.json()["task_id"]

    # Loop until we get the callback for *this* task_id (stale callbacks from prior tests may arrive first)
    deadline = time.time() + CALLBACK_WAIT
    while time.time() < deadline:
        callback_event.wait(timeout=min(10, deadline - time.time()))
        if callback_store.get("task_id") == task_id:
            break
        callback_event.clear()
    assert callback_store.get("task_id") == task_id, f"ไม่ได้รับ callback สำหรับ task {task_id} ภายใน {CALLBACK_WAIT}s"

    response = httpx.get(f"{BASE_URL}/tasks/{task_id}", headers=HEADERS, timeout=TIMEOUT)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data.get("status") in ("completed", "callback_success"), f"expected completed/callback_success, got: {data}"
    assert "results" in data, f"ต้องมี results หลัง completed: {data}"


def test_get_task_not_found():
    """task_id ที่ไม่มีอยู่ → 404"""
    response = httpx.get(
        f"{BASE_URL}/tasks/00000000-0000-0000-0000-000000000000",
        headers=HEADERS,
        timeout=TIMEOUT,
    )
    assert response.status_code == 404, response.text


def test_get_task_requires_auth():
    """GET /tasks/{id} โดยไม่ส่ง X-API-Key → 401"""
    response = httpx.get(
        f"{BASE_URL}/tasks/00000000-0000-0000-0000-000000000000",
        timeout=TIMEOUT,
    )
    assert response.status_code == 401, response.text
