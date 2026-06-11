import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import pytest


def test_health():
    from fastapi.testclient import TestClient
    from app.main import app
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert "version" in response.json()


def test_create_leave():
    from fastapi.testclient import TestClient
    from app.main import app
    client = TestClient(app)
    data = {
        "applicant": "测试用户",
        "department": "测试部门",
        "leave_type": "年假",
        "start_date": "2025-06-15T00:00:00",
        "end_date": "2025-06-17T00:00:00",
        "reason": "测试请假",
    }
    response = client.post("/api/leave/", json=data)
    assert response.status_code == 200
    assert response.json()["status"] == "待审批"


def test_get_leaves():
    from fastapi.testclient import TestClient
    from app.main import app
    client = TestClient(app)
    response = client.get("/api/leave/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_expense():
    from fastapi.testclient import TestClient
    from app.main import app
    client = TestClient(app)
    data = {
        "applicant": "测试用户",
        "department": "测试部门",
        "category": "差旅费",
        "amount": 3200.00,
        "description": "测试报销",
    }
    response = client.post("/api/expense/", json=data)
    assert response.status_code == 200


def test_meeting_rooms():
    from fastapi.testclient import TestClient
    from app.main import app
    client = TestClient(app)
    response = client.get("/api/meeting/rooms")
    assert response.status_code == 200
    rooms = response.json()
    assert len(rooms) >= 5


def test_announcements():
    from fastapi.testclient import TestClient
    from app.main import app
    client = TestClient(app)
    response = client.get("/api/announcement/")
    assert response.status_code == 200


def test_rag_init():
    from fastapi.testclient import TestClient
    from app.main import app
    client = TestClient(app)
    response = client.post("/api/agent/rag/init")
    assert response.status_code == 200
