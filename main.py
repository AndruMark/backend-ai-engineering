import os
from typing import Optional
from dotenv import load_dotenv
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be configured in environment variables.")

# Supabase Auth Client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI(
    title="Auth & Task API",
    description="Identity Provider Authentication (Supabase Auth) & Route Protection — Backend AI Engineering Track",
    version="4.0"
)

class AuthCredentials(BaseModel):
    email: Optional[str] = None
    password: Optional[str] = None

@app.get("/", tags=["System"], summary="API Root Metadata")
def read_root():
    return {
        "name": "Auth API",
        "version": "4.0",
        "auth_provider": "Supabase Auth",
        "endpoints": ["/auth/signup", "/auth/login", "/auth/logout", "/protected/profile", "/public/info", "/docs"]
    }

@app.get("/health", tags=["System"], summary="Server Health Check")
def health_check():
    return {"status": "ok", "supabase": "connected"}

@app.post("/auth/signup", status_code=status.HTTP_201_CREATED, tags=["Auth"], summary="Register new user")
def sign_up(payload: AuthCredentials):
    if not payload.email or not payload.email.strip() or not payload.password or not payload.password.strip():
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "Email and password are required"}
        )
    
    clean_email = payload.email.strip()
    clean_password = payload.password.strip()

    try:
        response = supabase.auth.sign_up({
            "email": clean_email,
            "password": clean_password
        })
        if not response.user:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "Unable to register user"}
            )
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "id": response.user.id,
                "email": response.user.email,
                "created_at": str(response.user.created_at)
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": str(e)}
        )

@app.post("/auth/login", status_code=status.HTTP_200_OK, tags=["Auth"], summary="Log in user and obtain JWT")
def log_in(payload: AuthCredentials):
    if not payload.email or not payload.email.strip() or not payload.password or not payload.password.strip():
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "Email and password are required"}
        )

    clean_email = payload.email.strip()
    clean_password = payload.password.strip()

    try:
        response = supabase.auth.sign_in_with_password({
            "email": clean_email,
            "password": clean_password
        })
        if not response.session or not response.session.access_token:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"error": "Invalid login credentials"}
            )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "access_token": response.session.access_token,
                "refresh_token": response.session.refresh_token,
                "token_type": "bearer",
                "user": {
                    "id": response.user.id,
                    "email": response.user.email
                }
            }
        )
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"error": "Invalid login credentials"}
        )

@app.get("/public/info", tags=["Public"], summary="Open public info endpoint")
def public_info():
    return {"message": "Welcome stranger! This info is public."}

@app.get("/protected/profile", tags=["Protected"], summary="Protected user profile (verified gate)")
def protected_profile(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"error": "Access token required"}
        )
    
    parts = auth_header.split(" ")
    if len(parts) != 2 or not parts[1].strip():
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"error": "Access token required"}
        )
        
    token = parts[1].strip()

    try:
        user_response = supabase.auth.get_user(token)
        if not user_response or not user_response.user:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"error": "Invalid or expired token"}
            )
        
        user = user_response.user
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "id": user.id,
                "email": user.email,
                "created_at": str(user.created_at)
            }
        )
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"error": "Invalid or expired token"}
        )
