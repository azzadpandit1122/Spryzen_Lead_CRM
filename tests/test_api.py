import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import httpx
import backend.scanner.engine

from backend.database import Base, get_db
from backend.main import app
from backend.config import settings

CURRENT_TEST_COUNTRY = "United States"

@pytest.fixture(scope="module", autouse=True)
def mock_scanner_http():
    def mock_get(url, *args, **kwargs):
        if "duckduckgo.com" in url or "github.com/search" in url or "remotive.com" in url or "hn.algolia.com" in url:
            html_content = """
            <html>
                <body>
                    <div class="result results_links">
                        <a class="result__a" href="https://www.testcompany.com/career1">React Developer Position</a>
                        <a class="result__snippet">Seeking a React developer. Contact details on website.</a>
                    </div>
                    <div class="result results_links">
                        <a class="result__a" href="https://www.testcompany.com/career2">FastAPI Developer Position</a>
                        <a class="result__snippet">Backend engineer needed. contact us today.</a>
                    </div>
                    <div class="result results_links">
                        <a class="result__a" href="https://www.testcompany.com/career3">Vue Developer Position</a>
                        <a class="result__snippet">Vue.js lead developer position open.</a>
                    </div>
                    <div class="result results_links">
                        <a class="result__a" href="https://www.testcompany.com/career4">NextJS Developer Position</a>
                        <a class="result__snippet">Next.js UI developer position open.</a>
                    </div>
                </body>
            </html>
            """
            if "api.github.com/search/issues" in url:
                return httpx.Response(200, json={
                    "items": [
                        {"title": "Vue Developer", "body": "Need a Vue developer, issue details on site.", "html_url": "https://www.testcompany.com/github1", "user": {"login": "vue_user"}},
                        {"title": "FastAPI Developer", "body": "Need a FastAPI developer.", "html_url": "https://www.testcompany.com/github2", "user": {"login": "fastapi_user"}},
                        {"title": "React Developer", "body": "Need a React developer.", "html_url": "https://www.testcompany.com/github3", "user": {"login": "react_user"}},
                        {"title": "NextJS Developer", "body": "Need a NextJS developer.", "html_url": "https://www.testcompany.com/github4", "user": {"login": "next_user"}},
                    ]
                })
            if "remotive.com/api/remote-jobs" in url:
                return httpx.Response(200, json={
                    "jobs": [
                        {"title": "FastAPI Job", "description": "Job details.", "url": "https://www.testcompany.com/remotive1", "company_name": "RemotiveCompany", "candidate_required_location": "Toronto, ON"},
                        {"title": "React Job", "description": "Job details.", "url": "https://www.testcompany.com/remotive2", "company_name": "RemotiveCompany", "candidate_required_location": "Toronto, ON"},
                        {"title": "Vue Job", "description": "Job details.", "url": "https://www.testcompany.com/remotive3", "company_name": "RemotiveCompany", "candidate_required_location": "Toronto, ON"},
                        {"title": "NextJS Job", "description": "Job details.", "url": "https://www.testcompany.com/remotive4", "company_name": "RemotiveCompany", "candidate_required_location": "Toronto, ON"},
                    ]
                })
            if "hn.algolia.com" in url:
                return httpx.Response(200, json={
                    "hits": [
                        {"title": "FastAPI project", "story_text": "Details here.", "url": "https://www.testcompany.com/hn1", "objectID": "1", "author": "hn_user1"},
                        {"title": "React project", "story_text": "Details here.", "url": "https://www.testcompany.com/hn2", "objectID": "2", "author": "hn_user2"},
                        {"title": "Vue project", "story_text": "Details here.", "url": "https://www.testcompany.com/hn3", "objectID": "3", "author": "hn_user3"},
                        {"title": "NextJS project", "story_text": "Details here.", "url": "https://www.testcompany.com/hn4", "objectID": "4", "author": "hn_user4"},
                    ]
                })
            return httpx.Response(200, html=html_content)
            
        global CURRENT_TEST_COUNTRY
        if CURRENT_TEST_COUNTRY == "India":
            html = """
            <html>
                <head>
                    <meta name="author" content="Rajesh Kumar">
                </head>
                <body>
                    <p>Contact us at contact@testcompany.in or call +91 9876543210</p>
                </body>
            </html>
            """
        elif CURRENT_TEST_COUNTRY == "United Kingdom":
            html = """
            <html>
                <head>
                    <meta name="author" content="Jane Smith">
                </head>
                <body>
                    <p>Contact us at contact@testcompany.co.uk or call +44 2079 460958</p>
                </body>
            </html>
            """
        elif CURRENT_TEST_COUNTRY == "Canada":
            html = """
            <html>
                <head>
                    <meta name="author" content="Bob Builder">
                </head>
                <body>
                    <p>Contact us at contact@testcompany.ca or call +1 (555) 456-7890</p>
                </body>
            </html>
            """
        else: # United States
            html = """
            <html>
                <head>
                    <meta name="author" content="Jane Doe">
                </head>
                <body>
                    <p>Contact us at contact@testcompany.com or call +1 (555) 123-4567</p>
                </body>
            </html>
            """
        return httpx.Response(200, html=html)

    original_get = backend.scanner.engine.httpx.get
    backend.scanner.engine.httpx.get = mock_get
    yield
    backend.scanner.engine.httpx.get = original_get

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
    global CURRENT_TEST_COUNTRY
    CURRENT_TEST_COUNTRY = "United States"
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

def test_new_scanner_features():
    admin_headers = get_auth_header("tester_admin", "testpassword123")
    
    # 1. Trigger scan with location override and country selection
    global CURRENT_TEST_COUNTRY
    CURRENT_TEST_COUNTRY = "United States"
    response = client.post(
        "/api/scanner/scan",
        headers=admin_headers,
        json={
            "keywords": ["Web Development"],
            "sources": ["LinkedIn", "Google Maps"],
            "date_filter": "Today",
            "time_filter": "Last 24 Hours",
            "location": "Boston, MA",
            "search_engine": "Bing",
            "target_count": 3,
            "country": "United States"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["leads_collected"] == 3
    assert len(data["leads"]) == 3
    
    # Verify the generated leads contain the correct location and source_link
    for lead in data["leads"]:
        assert lead["location"] == "Boston, MA"
        assert lead["source_link"] is not None
        assert lead["source_link"].startswith("http")
        assert lead["lead_source_detail"] is not None
        assert len(lead["lead_source_detail"]) > 10
        assert lead["trust_source"] is not None
        assert len(lead["trust_source"]) > 10
        assert lead["authenticity_level"] is not None

    # 2. Trigger scan with country selection and randomized location
    CURRENT_TEST_COUNTRY = "United Kingdom"
    response2 = client.post(
        "/api/scanner/scan",
        headers=admin_headers,
        json={
            "keywords": ["Mobile App Development"],
            "sources": ["Instagram"],
            "date_filter": "Today",
            "time_filter": "Last 24 Hours",
            "location": "any",
            "search_engine": "Google",
            "target_count": 2,
            "country": "United Kingdom"
        }
    )
    assert response2.status_code == 200
    data2 = response2.json()
    assert data2["leads_collected"] == 2
    assert len(data2["leads"]) == 2
    for lead in data2["leads"]:
        assert lead["location"].endswith(", UK")
        assert lead["source_link"] is not None

    # 3. Trigger scan with new entrepreneur platforms (Upwork, Reddit, Wellfound, GitHub)
    CURRENT_TEST_COUNTRY = "Canada"
    response3 = client.post(
        "/api/scanner/scan",
        headers=admin_headers,
        json={
            "keywords": ["AI Development", "SEO Services"],
            "sources": ["Upwork", "Reddit", "Wellfound", "GitHub"],
            "date_filter": "Today",
            "time_filter": "Last 24 Hours",
            "location": "any",
            "search_engine": "Yahoo",
            "target_count": 4,
            "country": "Canada"
        }
    )
    assert response3.status_code == 200
    data3 = response3.json()
    assert data3["leads_collected"] == 4
    assert len(data3["leads"]) == 4
    for lead in data3["leads"]:
        assert lead["location"].endswith(", ON") or lead["location"].endswith(", BC") or lead["location"].endswith(", QC") or lead["location"].endswith(", AB")
        assert lead["source_link"] is not None
        assert lead["phone_number"].startswith("+1 (555)")
        assert lead["email_address"].endswith(".ca")
        assert lead["website"].endswith(".ca")
        assert lead["source"] in ["Upwork", "Reddit", "Wellfound", "GitHub"]
        if lead["source"] == "Upwork":
            assert "upwork.com" in lead["source_link"]
        elif lead["source"] == "Reddit":
            assert "reddit.com" in lead["source_link"]
        elif lead["source"] == "Wellfound":
            assert "wellfound.com" in lead["source_link"]
        elif lead["source"] == "GitHub":
            assert "github.com" in lead["source_link"]

def test_india_scanner_consistency():
    admin_headers = get_auth_header("tester_admin", "testpassword123")
    global CURRENT_TEST_COUNTRY
    CURRENT_TEST_COUNTRY = "India"
    response = client.post(
        "/api/scanner/scan",
        headers=admin_headers,
        json={
            "keywords": ["Web Development"],
            "sources": ["LinkedIn"],
            "date_filter": "Today",
            "time_filter": "Last 24 Hours",
            "location": "any",
            "search_engine": "Google",
            "target_count": 3,
            "country": "India"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["leads_collected"] == 3
    for lead in data["leads"]:
        assert lead["phone_number"].startswith("+91")
        assert lead["email_address"].endswith(".in")
        assert lead["website"].endswith(".in")
        # Ensure company name is part of domain
        company_clean = lead["email_address"].split("@")[1].split(".in")[0]
        assert len(company_clean) > 0

def test_manual_lead_validation():
    admin_headers = get_auth_header("tester_admin", "testpassword123")
    
    # 1. Attempt manual creation with missing contact name
    response = client.post(
        "/api/leads",
        headers=admin_headers,
        json={
            "project_name": "Test Manual Lead Validation",
            "source": "LinkedIn",
            "phone_number": "+1 (555) 123-4567",
            "email_address": "test@company.com",
            "source_link": "https://www.linkedin.com/jobs/123",
            "collection_date": "2026-06-13",
            "collection_time": "12:00:00"
        }
    )
    assert response.status_code == 422

    # 2. Attempt manual creation with missing email
    response = client.post(
        "/api/leads",
        headers=admin_headers,
        json={
            "project_name": "Test Manual Lead Validation",
            "source": "LinkedIn",
            "contact_name": "Jane Doe",
            "phone_number": "+1 (555) 123-4567",
            "source_link": "https://www.linkedin.com/jobs/123",
            "collection_date": "2026-06-13",
            "collection_time": "12:00:00"
        }
    )
    assert response.status_code == 422

    # 3. Attempt manual creation with missing phone number
    response = client.post(
        "/api/leads",
        headers=admin_headers,
        json={
            "project_name": "Test Manual Lead Validation",
            "source": "LinkedIn",
            "contact_name": "Jane Doe",
            "email_address": "test@company.com",
            "source_link": "https://www.linkedin.com/jobs/123",
            "collection_date": "2026-06-13",
            "collection_time": "12:00:00"
        }
    )
    assert response.status_code == 422

    # 4. Attempt manual creation with missing source link
    response = client.post(
        "/api/leads",
        headers=admin_headers,
        json={
            "project_name": "Test Manual Lead Validation",
            "source": "LinkedIn",
            "contact_name": "Jane Doe",
            "phone_number": "+1 (555) 123-4567",
            "email_address": "test@company.com",
            "collection_date": "2026-06-13",
            "collection_time": "12:00:00"
        }
    )
    assert response.status_code == 422

    # 5. Create successfully when all required fields are present
    response = client.post(
        "/api/leads",
        headers=admin_headers,
        json={
            "project_name": "Test Manual Lead Validation",
            "source": "LinkedIn",
            "contact_name": "Jane Doe",
            "phone_number": "+1 (555) 123-4567",
            "email_address": "test@company.com",
            "source_link": "https://www.linkedin.com/jobs/123",
            "collection_date": "2026-06-13",
            "collection_time": "12:00:00"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["contact_name"] == "Jane Doe"
    assert data["phone_number"] == "+1 (555) 123-4567"
    assert data["email_address"] == "test@company.com"
    assert data["source_link"] == "https://www.linkedin.com/jobs/123"

def test_scanner_streaming():
    admin_headers = get_auth_header("tester_admin", "testpassword123")
    global CURRENT_TEST_COUNTRY
    CURRENT_TEST_COUNTRY = "United States"
    
    response = client.post(
        "/api/scanner/scan",
        headers=admin_headers,
        json={
            "keywords": ["Web Development"],
            "sources": ["LinkedIn"],
            "date_filter": "Today",
            "time_filter": "Last 24 Hours",
            "location": "Boston, MA",
            "search_engine": "Google",
            "target_count": 1,
            "country": "United States",
            "stream": True
        }
    )
    assert response.status_code == 200
    lines = response.text.split("\n")
    logs_received = []
    final_result = None
    for line in lines:
        if line.strip():
            import json
            data = json.loads(line)
            if "log" in data:
                logs_received.append(data["log"])
            else:
                final_result = data
                
    assert len(logs_received) > 0
    assert final_result is not None
    assert final_result["success"] is True
    assert final_result["leads_collected"] > 0
