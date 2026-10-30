import os
from dotenv import load_dotenv
from fastapi import FastAPI
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be configured in environment variables.")

# Supabase Auth Client Initialization
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI(
    title="Auth & Task API",
    description="Identity Provider Authentication (Supabase Auth) & Route Protection — Backend AI Engineering Track",
    version="4.0"
)

@app.on_event("startup")
def startup_event():
    print("Server running and connected to Supabase Auth client.")

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
