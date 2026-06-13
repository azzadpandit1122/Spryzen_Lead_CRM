from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import os

from backend.config import settings
from backend.database import engine, Base, SessionLocal
from backend.models import User
from backend.auth_utils import get_password_hash
from backend.api import auth, leads, reminders, users, scanner, reports

# Create all database tables if they do not exist
Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.PROJECT_NAME)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Seed default admin user on startup if database is empty
@app.on_event("startup")
def startup_event():
    db = SessionLocal()
    try:
        admin_user = db.query(User).filter(User.username == settings.DEFAULT_ADMIN_USERNAME).first()
        if not admin_user:
            # Create default admin user
            admin = User(
                username=settings.DEFAULT_ADMIN_USERNAME,
                email=settings.DEFAULT_ADMIN_EMAIL,
                password_hash=get_password_hash(settings.DEFAULT_ADMIN_PASSWORD),
                role="admin",
                full_name="System Administrator"
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)
            print(f"Created default admin user: {settings.DEFAULT_ADMIN_USERNAME} / {settings.DEFAULT_ADMIN_PASSWORD}")
    except Exception as e:
        print(f"Error seeding database: {e}")
    finally:
        db.close()

# Include API Routers
app.include_router(auth.router)
app.include_router(leads.router)
app.include_router(reminders.router)
app.include_router(users.router)
app.include_router(scanner.router)
app.include_router(reports.router)

# Mount Frontend Static Files at the root
# Note: This must be mounted AFTER routes, otherwise it overrides them
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
else:
    print(f"Warning: Frontend directory '{frontend_dir}' not found. Serving API endpoints only.")
