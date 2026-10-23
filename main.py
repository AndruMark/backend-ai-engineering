from fastapi import FastAPI, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List

app = FastAPI(
    title="Task API",
    description="In-memory CRUD Task Management API — Backend AI Engineering Track",
    version="1.0"
)

tasks_db = [
    {"id": 1, "title": "Setup development environment with Scoop and Python", "done": True},
    {"id": 2, "title": "Build CRUD endpoints with FastAPI", "done": False},
    {"id": 3, "title": "Test endpoints via Swagger UI and cURL", "done": False}
]

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
        "version": "1.0",
        "endpoints": ["/tasks", "/tasks/{id}", "/health", "/docs"]
    }

@app.get("/health", tags=["System"], summary="Server Health Check")
def health_check():
    return {"status": "ok"}

@app.get("/tasks", response_model=List[TaskResponse], tags=["Tasks"], summary="Get all tasks")
def get_all_tasks():
    return tasks_db

@app.get("/tasks/{task_id}", response_model=TaskResponse, tags=["Tasks"], summary="Get task by ID")
def get_task(task_id: int):
    for task in tasks_db:
        if task["id"] == task_id:
            return task
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"error": f"Task {task_id} not found"}
    )

@app.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED, tags=["Tasks"], summary="Create a new task")
def create_task(payload: TaskCreate):
    cleaned_title = payload.title.strip()
    if not cleaned_title:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "Title is required and cannot be empty"}
        )

    next_id = max([t["id"] for t in tasks_db], default=0) + 1
    new_task = {
        "id": next_id,
        "title": cleaned_title,
        "done": False
    }
    tasks_db.append(new_task)
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=new_task)

@app.put("/tasks/{task_id}", response_model=TaskResponse, tags=["Tasks"], summary="Update task")
def update_task(task_id: int, payload: TaskUpdate):
    for task in tasks_db:
        if task["id"] == task_id:
            if payload.title is None and payload.done is None:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"error": "Request body must include 'title' or 'done'"}
                )
            if payload.title is not None:
                cleaned_title = payload.title.strip()
                if not cleaned_title:
                    return JSONResponse(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        content={"error": "Title cannot be empty"}
                    )
                task["title"] = cleaned_title
            if payload.done is not None:
                task["done"] = payload.done
            return task

    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"error": f"Task {task_id} not found"}
    )

@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Tasks"], summary="Delete task")
def delete_task(task_id: int):
    for index, task in enumerate(tasks_db):
        if task["id"] == task_id:
            tasks_db.pop(index)
            return Response(status_code=status.HTTP_204_NO_CONTENT)

    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"error": f"Task {task_id} not found"}
    )
