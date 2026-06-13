import os

class Settings:
    PROJECT_NAME: str = "ClinetHub"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "7b9d62bb4e1837a7b82f0c7e26da7eef40bcf3f1e944bc3a4d46b7a974bfa55a")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120
    
    # SQLite Database URL
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./clinethub.db")
    
    # Default Admin account setup
    DEFAULT_ADMIN_USERNAME: str = "admin"
    DEFAULT_ADMIN_EMAIL: str = "admin@clinethub.com"
    DEFAULT_ADMIN_PASSWORD: str = "admin123"

settings = Settings()
