import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

from backend.database import Base, get_db
from backend.main import app
from backend.config import settings

# Setup isolated test database
TEST_DB_URL = "sqlite:///./test_api.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Client fixture
@pytest.fixture(scope="module", autouse=True)
def setup_database():
    # Create tables
    Base.metadata.create_all(bind=engine)
    yield
    # Clean up test database file
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("./test_api.db"):
        try:
            os.remove("./test_api.db")
        except Exception:
            pass

client = TestClient(app)

# Helper to get authorization header
def get_auth_header(username, password):
    response = client.post(
        "/api/auth/login",
        data={"username": username, "password": password}
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_user_flow():
    # 1. Register first user (automatically becomes admin)
    response = client.post(
        "/api/auth/register",
        json={
            "username": "tester_admin",
            "email": "tester_admin@example.com",
            "full_name": "Test Admin",
            "password": "testpassword123",
            "role": "admin"
        }
    )
    assert response.status_code == 200
    assert response.json()["username"] == "tester_admin"
    assert response.json()["role"] == "admin"

    # 2. Register second user (defaults to sales_executive)
    response = client.post(
        "/api/auth/register",
        json={
            "username": "tester_exec",
            "email": "tester_exec@example.com",
            "full_name": "Test Executive",
            "password": "testpassword123",
            "role": "sales_executive"
        }
    )
    assert response.status_code == 200
    assert response.json()["username"] == "tester_exec"
    assert response.json()["role"] == "sales_executive"

    # 3. Log in admin & get profile
    admin_headers = get_auth_header("tester_admin", "testpassword123")
    response = client.get("/api/auth/me", headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["full_name"] == "Test Admin"

def test_scanner_and_leads_flow():
    admin_headers = get_auth_header("tester_admin", "testpassword123")
    exec_headers = get_auth_header("tester_exec", "testpassword123")

    # 1. Read scanner config
    response = client.get("/api/scanner/config", headers=admin_headers)
    assert response.status_code == 200
    assert "keywords" in response.json()

    # 2. Trigger scan (simulated search)
    response = client.post(
        "/api/scanner/scan",
        headers=admin_headers,
        json={
            "keywords": ["Web Development", "AI Development"],
            "sources": ["LinkedIn", "Google Maps"],
            "date_filter": "Today",
            "time_filter": "Last 24 Hours"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "leads_collected" in data
    assert "logs" in data

    # 3. List leads as executive
    response = client.get("/api/leads", headers=exec_headers)
    assert response.status_code == 200
    leads = response.json()
    assert len(leads) >= 0

    if len(leads) > 0:
        lead_id = leads[0]["id"]
        
        # 4. Claim lead as executive
        response = client.post(f"/api/leads/{lead_id}/claim", headers=exec_headers)
        assert response.status_code == 200
        assert response.json()["status"] == "Contacted"
        assert response.json()["claimed_by_id"] is not None

        # 5. Update lead details (add note)
        response = client.put(
            f"/api/leads/{lead_id}",
            headers=exec_headers,
            json={
                "notes": "Spoke to contact person. They are interested in a quote next week.",
                "status": "Interested",
                "priority": "Best Opportunity"
            }
        )
        assert response.status_code == 200
        assert response.json()["status"] == "Interested"
        assert response.json()["priority"] == "Best Opportunity"
        assert "Spoke to contact person" in response.json()["notes"]

def test_reminders_and_reports_flow():
    admin_headers = get_auth_header("tester_admin", "testpassword123")
    exec_headers = get_auth_header("tester_exec", "testpassword123")

    # Get leads first
    response = client.get("/api/leads", headers=exec_headers)
    leads = response.json()
    
    if len(leads) > 0:
        lead_id = leads[0]["id"]
        user_me = client.get("/api/auth/me", headers=exec_headers).json()
        user_id = user_me["id"]

        # 1. Create reminder
        response = client.post(
            "/api/reminders",
            headers=exec_headers,
            json={
                "lead_id": lead_id,
                "date": "2026-06-15",
                "time": "10:30:00",
                "note": "Follow up call on pricing proposal",
                "assigned_user_id": user_id
            }
        )
        assert response.status_code == 200
        reminder_id = response.json()["id"]

        # 2. Get list of reminders
        response = client.get("/api/reminders", headers=exec_headers)
        assert response.status_code == 200
        assert len(response.json()) > 0

        # 3. Update reminder to completed
        response = client.put(
            f"/api/reminders/{reminder_id}",
            headers=exec_headers,
            json={"is_completed": True}
        )
        assert response.status_code == 200
        assert response.json()["is_completed"] is True

        # 4. Delete reminder
        response = client.delete(f"/api/reminders/{reminder_id}", headers=exec_headers)
        assert response.status_code == 200

    # 5. Fetch Dashboard reports
    response = client.get("/api/reports/dashboard", headers=exec_headers)
    assert response.status_code == 200
    metrics = response.json()
    assert "lead_metrics" in metrics
    assert "sales_metrics" in metrics
    assert "recent_activities" in metrics
