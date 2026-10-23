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

init_db()

app = FastAPI(
    title="Task API",
    description="Persistent CRUD Task Management API with SQLite — Backend AI Engineering Track",
    version="2.0"
)

class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, description="Task title cannot be empty")

class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, description="Task title")
    done: Optional[bool] = Field(None, description="Completion status")

class TaskResponse(BaseModel):
    id: int
    title: str
    done: bool

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

@app.get("/tasks", response_model=List[TaskResponse], tags=["Tasks"], summary="Get all tasks")
def get_all_tasks():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, done FROM tasks")
    rows = cursor.fetchall()
    conn.close()
    return [{"id": row["id"], "title": row["title"], "done": bool(row["done"])} for row in rows]

@app.get("/tasks/{task_id}", response_model=TaskResponse, tags=["Tasks"], summary="Get task by ID")
def get_task(task_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, done FROM tasks WHERE id = ?", (task_id,))
    row = cursor.fetchone()
    conn.close()
    if row is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": f"Task {task_id} not found"}
        )
    return {"id": row["id"], "title": row["title"], "done": bool(row["done"])}

@app.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED, tags=["Tasks"], summary="Create a new task")
def create_task(payload: TaskCreate):
    cleaned_title = payload.title.strip()
    if not cleaned_title:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "Title is required and cannot be empty"}
        )

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO tasks (title, done) VALUES (?, ?)",
        (cleaned_title, 0)
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()

    new_task = {
        "id": new_id,
        "title": cleaned_title,
        "done": False
    }
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=new_task)

@app.put("/tasks/{task_id}", response_model=TaskResponse, tags=["Tasks"], summary="Update task")
def update_task(task_id: int, payload: TaskUpdate):
    if payload.title is None and payload.done is None:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "Request body must include 'title' or 'done'"}
        )

    cleaned_title = None
    if payload.title is not None:
        cleaned_title = payload.title.strip()
        if not cleaned_title:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "Title cannot be empty"}
            )

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, done FROM tasks WHERE id = ?", (task_id,))
    row = cursor.fetchone()

    if row is None:
        conn.close()
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": f"Task {task_id} not found"}
        )

    updated_title = cleaned_title if cleaned_title is not None else row["title"]
    updated_done = int(payload.done) if payload.done is not None else row["done"]

    cursor.execute(
        "UPDATE tasks SET title = ?, done = ? WHERE id = ?",
        (updated_title, updated_done, task_id)
    )
    conn.commit()
    conn.close()

    return {
        "id": task_id,
        "title": updated_title,
        "done": bool(updated_done)
    }

@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Tasks"], summary="Delete task")
def delete_task(task_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    rows_affected = cursor.rowcount
    conn.close()

    if rows_affected == 0:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": f"Task {task_id} not found"}
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)
