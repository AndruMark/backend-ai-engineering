import sqlite3
from fastapi import FastAPI, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List

DB_FILE = "tasks.db"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            done BOOLEAN NOT NULL DEFAULT 0
        )
    """)
    conn.commit()

    # Seed 3 initial tasks only if the table is empty
    cursor.execute("SELECT COUNT(*) FROM tasks")
    count = cursor.fetchone()[0]
    if count == 0:
        cursor.executemany(
            "INSERT INTO tasks (title, done) VALUES (?, ?)",
            [
                ("Setup development environment with Scoop and Python", 1),
                ("Build CRUD endpoints with FastAPI", 0),
                ("Test endpoints via Swagger UI and cURL", 0)
            ]
        )
        conn.commit()
    conn.close()

# Initialize database schema and seeds on startup
init_db()

app = FastAPI(
    title="Task API",
    description="Persistent CRUD Task Management API with SQLite — Backend AI Engineering Track",
    version="2.0"
)

@app.get("/", tags=["System"], summary="API Root Metadata")
def read_root():
    return {
        "name": "Task API",
        "version": "2.0",
        "storage": "SQLite",
        "endpoints": ["/tasks", "/tasks/{id}", "/health", "/docs"]
    }

@app.get("/health", tags=["System"], summary="Server Health Check")
def health_check():
    return {"status": "ok"}
