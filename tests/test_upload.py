"""Tests for POST /uploadimage and /uploadimage/batch"""

import httpx
import pytest

from conftest import BASE_URL, HEADERS, IMAGE_PATH, SYNC_TIMEOUT as TIMEOUT


def _assert_meter_response(data: dict):
    """ตรวจสอบ schema ของ MeterResponse"""
    assert "data" in data, "missing data"
    assert "warnings" in data, "missing warnings"
    assert isinstance(data["data"], dict)
    assert "meterId" in data["data"], "missing data.meterId"
    assert "value" in data["data"], "missing data.value"
    assert isinstance(data["warnings"], list)


# ─── /uploadimage ─────────────────────────────────────────────────────────────


def test_upload_single_success():
    """อัปโหลด 1 ไฟล์ → ได้ MeterResponse ที่ครบถ้วน"""
    with open(IMAGE_PATH, "rb") as f:
        response = httpx.post(
            f"{BASE_URL}/uploadimage",
            files={"file": ("example.jpg", f, "image/jpeg")},
            headers=HEADERS,
            timeout=TIMEOUT,
        )
    assert response.status_code == 200, response.text
    _assert_meter_response(response.json())


def test_upload_single_value_is_number():
    """ตรวจว่า data.value เป็น number (ไม่ใช่ string)"""
    with open(IMAGE_PATH, "rb") as f:
        response = httpx.post(
            f"{BASE_URL}/uploadimage",
            files={"file": ("example.jpg", f, "image/jpeg")},
            headers=HEADERS,
            timeout=TIMEOUT,
        )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["data"]["value"], (int, float))


def test_upload_missing_file():
    """ไม่แนบ file → 422 Validation Error"""
    response = httpx.post(f"{BASE_URL}/uploadimage", headers=HEADERS, timeout=TIMEOUT)
    assert response.status_code == 422


def test_upload_no_api_key_returns_401():
    """ไม่ส่ง X-API-Key → 401 Unauthorized"""
    with open(IMAGE_PATH, "rb") as f:
        response = httpx.post(
            f"{BASE_URL}/uploadimage",
            files={"file": ("example.jpg", f, "image/jpeg")},
            timeout=TIMEOUT,
        )
    assert response.status_code == 401, response.text


def test_upload_wrong_api_key_returns_401():
    """ส่ง X-API-Key ผิด → 401 Unauthorized"""
    with open(IMAGE_PATH, "rb") as f:
        response = httpx.post(
            f"{BASE_URL}/uploadimage",
            files={"file": ("example.jpg", f, "image/jpeg")},
            headers={"X-API-Key": "wrong-key"},
            timeout=TIMEOUT,
        )
    assert response.status_code == 401, response.text


# ─── /uploadimage/batch ───────────────────────────────────────────────────────


def test_upload_batch_success():
    """อัปโหลด 2 ไฟล์พร้อมกัน → ได้ array ขนาด 2"""
    with open(IMAGE_PATH, "rb") as f1, open(IMAGE_PATH, "rb") as f2:
        response = httpx.post(
            f"{BASE_URL}/uploadimage/batch",
            files=[
                ("files", ("example_1.jpg", f1, "image/jpeg")),
                ("files", ("example_2.jpg", f2, "image/jpeg")),
            ],
            headers=HEADERS,
            timeout=TIMEOUT,
        )
    assert response.status_code == 200, response.text
    results = response.json()
    assert isinstance(results, list)
    assert len(results) == 2
    for item in results:
        _assert_meter_response(item)


def test_upload_batch_single_item():
    """batch ด้วย 1 ไฟล์ → array ขนาด 1"""
    with open(IMAGE_PATH, "rb") as f:
        response = httpx.post(
            f"{BASE_URL}/uploadimage/batch",
            files=[("files", ("example.jpg", f, "image/jpeg"))],
            headers=HEADERS,
            timeout=TIMEOUT,
        )
    assert response.status_code == 200
    results = response.json()
    assert isinstance(results, list)
    assert len(results) == 1


def test_upload_batch_missing_files():
    """ไม่แนบไฟล์เลยใน batch → 422"""
    response = httpx.post(f"{BASE_URL}/uploadimage/batch", headers=HEADERS, timeout=TIMEOUT)
    assert response.status_code == 422
