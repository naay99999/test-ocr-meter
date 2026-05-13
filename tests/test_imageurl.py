"""Tests for POST /imageurl and /imageurl/batch"""

import httpx
import pytest

from conftest import BASE_URL, HEADERS, IMAGE_URL, SYNC_TIMEOUT as TIMEOUT


def _assert_meter_response(data: dict):
    assert "data" in data
    assert "warnings" in data
    assert isinstance(data["data"], dict)
    assert "meterId" in data["data"]
    assert "value" in data["data"]
    assert isinstance(data["warnings"], list)


# ─── /imageurl ────────────────────────────────────────────────────────────────


def test_imageurl_single_success():
    """ส่ง image_url → ได้ MeterResponse ครบถ้วน"""
    payload = {"image_url": IMAGE_URL}
    response = httpx.post(f"{BASE_URL}/imageurl", json=payload, headers=HEADERS, timeout=TIMEOUT)
    assert response.status_code == 200, response.text
    _assert_meter_response(response.json())


def test_imageurl_with_overlay():
    """ส่งพร้อม overlay coordinates → API ต้องรับ parameter ได้ ไม่ crash (200 หรือ 422 ขึ้นกับพื้นที่ที่ตัด)"""
    payload = {
        "image_url": IMAGE_URL,
        "overlay": {
            "overlay_top": 0,
            "overlay_left": 0,
            "overlay_width": 500,
            "overlay_height": 500,
        },
    }
    response = httpx.post(f"{BASE_URL}/imageurl", json=payload, headers=HEADERS, timeout=TIMEOUT)
    assert response.status_code in (200, 422), response.text


def test_imageurl_with_gauge_params():
    """ส่ง gauge_min / gauge_max (legacy params) → ต้องไม่พัง"""
    payload = {
        "image_url": IMAGE_URL,
        "gauge_min": 0,
        "gauge_max": 100,
    }
    response = httpx.post(f"{BASE_URL}/imageurl", json=payload, headers=HEADERS, timeout=TIMEOUT)
    assert response.status_code == 200, response.text
    _assert_meter_response(response.json())


def test_imageurl_bad_url():
    """URL ที่ไม่มีรูป → 400 หรือ 200 with is_success=false"""
    payload = {"image_url": "https://httpbin.org/status/404"}
    response = httpx.post(f"{BASE_URL}/imageurl", json=payload, headers=HEADERS, timeout=TIMEOUT)
    assert response.status_code in (200, 400), response.text
    if response.status_code == 200:
        data = response.json()
        assert data["is_success"] is False


def test_imageurl_missing_field():
    """ไม่ส่ง image_url → 422"""
    response = httpx.post(f"{BASE_URL}/imageurl", json={}, headers=HEADERS, timeout=TIMEOUT)
    assert response.status_code == 422


def test_imageurl_invalid_url_format():
    """image_url ไม่ใช่ URL จริง → 422"""
    payload = {"image_url": "not-a-url"}
    response = httpx.post(f"{BASE_URL}/imageurl", json=payload, headers=HEADERS, timeout=TIMEOUT)
    assert response.status_code == 422


def test_imageurl_no_api_key_returns_401():
    """ไม่ส่ง X-API-Key → 401 Unauthorized"""
    payload = {"image_url": IMAGE_URL}
    response = httpx.post(f"{BASE_URL}/imageurl", json=payload, timeout=TIMEOUT)
    assert response.status_code == 401, response.text


def test_imageurl_wrong_api_key_returns_401():
    """ส่ง X-API-Key ผิด → 401 Unauthorized"""
    payload = {"image_url": IMAGE_URL}
    response = httpx.post(
        f"{BASE_URL}/imageurl", json=payload, headers={"X-API-Key": "wrong-key"}, timeout=TIMEOUT
    )
    assert response.status_code == 401, response.text


# ─── /imageurl/batch ──────────────────────────────────────────────────────────


def test_imageurl_batch_success():
    """ส่ง 2 URLs พร้อมกัน → array ขนาด 2"""
    payloads = [
        {"image_url": IMAGE_URL},
        {"image_url": IMAGE_URL},
    ]
    response = httpx.post(f"{BASE_URL}/imageurl/batch", json=payloads, headers=HEADERS, timeout=TIMEOUT)
    assert response.status_code == 200, response.text
    results = response.json()
    assert isinstance(results, list)
    assert len(results) == 2
    for item in results:
        _assert_meter_response(item)


def test_imageurl_batch_single_item():
    """batch ด้วย 1 URL → array ขนาด 1"""
    payloads = [{"image_url": IMAGE_URL}]
    response = httpx.post(f"{BASE_URL}/imageurl/batch", json=payloads, headers=HEADERS, timeout=TIMEOUT)
    assert response.status_code == 200
    results = response.json()
    assert isinstance(results, list)
    assert len(results) == 1


def test_imageurl_batch_empty_array():
    """ส่ง array ว่าง → 422 หรือ 200 with empty array"""
    response = httpx.post(f"{BASE_URL}/imageurl/batch", json=[], headers=HEADERS, timeout=TIMEOUT)
    assert response.status_code in (200, 422), response.text
