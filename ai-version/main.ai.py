# Naive AI Authentication Implementation
# Issues: trusts token blindly, missing whitespace validation, no uniform custom error JSON
from fastapi import FastAPI, Header, HTTPException
from supabase import create_client

supabase = create_client("https://dummy.supabase.co", "dummy_key")
app = FastAPI()

@app.post("/auth/signup")
def signup(data: dict):
    # Naive: does not check for empty or whitespace-only strings
    return supabase.auth.sign_up({"email": data["email"], "password": data["password"]})

@app.post("/auth/login")
def login(data: dict):
    # Naive: does not distinguish 400 from 401
    return supabase.auth.sign_in_with_password({"email": data["email"], "password": data["password"]})

@app.get("/protected/profile")
def profile(authorization: str = Header(None)):
    # Flaw: raw string split without bounds check, crashes on malformed header
    token = authorization.split(" ")[1]
    user = supabase.auth.get_user(token)
    return user
