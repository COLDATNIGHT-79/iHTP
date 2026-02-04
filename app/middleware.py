import uuid
import hashlib
import os
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.secret_key = os.getenv("SECRET_KEY", "dev-secret-do-not-use-in-prod")

    async def dispatch(self, request: Request, call_next):
        # 1. Get Cookie
        anon_id = request.cookies.get("anon_id")
        new_cookie = False

        # 2. If missing, generate new
        if not anon_id:
            anon_id = str(uuid.uuid4())
            new_cookie = True
        
        # 3. Attach hashed ID to request state for endpoints to use
        # Hash formula: SHA256(anon_id + SECRET)
        # We hash it so we never work with the raw ID in our logic/database
        hash_input = f"{anon_id}{self.secret_key}".encode()
        user_hash = hashlib.sha256(hash_input).hexdigest()
        
        request.state.user_hash = user_hash
        
        # 4. Process Request
        response = await call_next(request)
        
        # 5. Set Cookie if new
        if new_cookie:
            response.set_cookie(
                key="anon_id", 
                value=anon_id,
                httponly=True,
                secure=False, # Set to True in Production (HTTPS)
                samesite="lax",
                max_age=315360000 # 10 years
            )
            
        return response
