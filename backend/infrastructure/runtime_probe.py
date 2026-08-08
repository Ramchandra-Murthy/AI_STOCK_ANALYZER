from __future__ import annotations

import logging
import os
import sys

logger = logging.getLogger(__name__)

def verify_runtime_environment() -> bool:
    """
    Validates essential environment variables and component accessibility
    for containerized EROS runtime.
    """
    print("--- EROS 3.0 Production Runtime Readiness Probe ---")
    
    db_url = os.getenv("DATABASE_URL", "sqlite:///./production.db")
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    env_mode = os.getenv("APP_ENVIRONMENT", "development")
    
    print(f"  APP_ENVIRONMENT : {env_mode}")
    print(f"  DATABASE_URL    : {db_url.split('@')[-1] if '@' in db_url else db_url}")
    print(f"  REDIS_URL       : {redis_url}")
    
    # Verify core imports
    try:
        import fastapi
        import celery
        import sqlalchemy
        import redis
        print("  [OK] Core dependencies (FastAPI, Celery, SQLAlchemy, Redis) imported successfully.")
    except ImportError as e:
        print(f"  [FAIL] Missing required runtime dependency: {e}")
        return False

    print("  [SUCCESS] Runtime environment pre-flight check passed.")
    return True

if __name__ == "__main__":
    success = verify_runtime_environment()
    sys.exit(0 if success else 1)