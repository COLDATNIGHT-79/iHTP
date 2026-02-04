import os
import hashlib
import secrets
from jose import JWTError, jwt
from datetime import datetime, timedelta
from fastapi import Request, HTTPException

# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-do-not-use-in-prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Admin password hash (stored in .env as ADMIN_PASSWORD_HASH)
# This is a SHA256 hash of your password
# To generate: python -c "import hashlib; print(hashlib.sha256('your_password'.encode()).hexdigest())"
ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH", "")

def verify_password(plain_password: str) -> bool:
    """Verify password against stored hash"""
    if not ADMIN_PASSWORD_HASH:
        return False
    input_hash = hashlib.sha256(plain_password.encode()).hexdigest()
    return secrets.compare_digest(input_hash, ADMIN_PASSWORD_HASH)

def create_access_token(data: dict) -> str:
    """Create JWT token for admin session"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_admin_token(token: str) -> bool:
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("admin") == True
    except JWTError:
        return False

def get_admin_from_cookie(request: Request) -> bool:
    """Check if admin token exists in cookies"""
    token = request.cookies.get("admin_token")
    if not token:
        return False
    return verify_admin_token(token)

def require_admin(request: Request):
    """Dependency to require admin authentication"""
    if not get_admin_from_cookie(request):
        raise HTTPException(status_code=401, detail="Admin authentication required")
    return True
