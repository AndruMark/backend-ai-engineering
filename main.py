import os
import psycopg
from psycopg.rows import dict_row
from fastapi import FastAPI, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:dev@localhost:5432/tasks")

def get_db_connection():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)

def init_db():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id SERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    done BOOLEAN NOT NULL DEFAULT FALSE
                );
            """)
            cur.execute("SELECT COUNT(*) AS count FROM tasks;")
            row = cur.fetchone()
            if row["count"] == 0:
                cur.executemany(
                    "INSERT INTO tasks (title, done) VALUES (%s, %s);",
                    [
                        ("Setup development environment with Scoop and Python", True),
                        ("Build CRUD endpoints with FastAPI", False),
                        ("Test endpoints via Swagger UI and cURL", False)
                    ]
                )
            conn.commit()

init_db()

app = FastAPI(
    title="Task API",
    description="Containerized PostgreSQL Task Management API — Backend AI Engineering Track",
    version="3.0"
)

class TaskResponse(BaseModel):
    id: int
    title: str
    done: bool

@app.get("/", tags=["System"], summary="API Root Metadata")
def read_root():
    return {
        "name": "Task API",
        "version": "3.0",
        "storage": "PostgreSQL",
        "endpoints": ["/tasks", "/tasks/{id}", "/health", "/docs"]
    }

@app.get("/health", tags=["System"], summary="Server Health Check")
def health_check():
    return {"status": "ok"}

@app.get("/tasks", response_model=List[TaskResponse], tags=["Tasks"], summary="Get all tasks")
def get_all_tasks():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, title, done FROM tasks ORDER BY id ASC;")
            return cur.fetchall()

@app.get("/tasks/{task_id}", response_model=TaskResponse, tags=["Tasks"], summary="Get task by ID")
def get_task(task_id: int):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, title, done FROM tasks WHERE id = %s;", (task_id,))
            row = cur.fetchone()
            if not row:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={"error": "Task not found"}
                )
            return row
