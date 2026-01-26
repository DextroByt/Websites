from fastapi import Security, HTTPException, status
from fastapi.security.api_key import APIKeyHeader
from sqlalchemy.orm import Session
from database_setup import Session as DBSession, APIKey

api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)

async def get_api_key(api_key_header: str = Security(api_key_header)):
    """
    Validates the API Key from the header.
    Returns the APIKey object if valid, else raises 401.
    """
    if not api_key_header:
        # Check if it's a browser session (optional, for dashboard access)
        # For now, we enforce API keys for API routes.
        # Dashboard routes won't use this dependency.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API Key",
        )

    db = DBSession()
    try:
        key_record = db.query(APIKey).filter(APIKey.key == api_key_header, APIKey.is_active == True).first()
        if not key_record:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid or Inactive API Key",
            )
        return key_record
    finally:
        db.close()

def get_db():
    db = DBSession()
    try:
        yield db
    finally:
        db.close()
