from fastapi import FastAPI, status
from fastapi.responses import JSONResponse

app = FastAPI(title="Task API", version="1.0")

# In-Memory Database Seed (3 tareas iniciales)
tasks_db = [
    {"id": 1, "title": "Setup development environment with Scoop and Python", "done": True},
    {"id": 2, "title": "Build CRUD endpoints with FastAPI", "done": False},
    {"id": 3, "title": "Test endpoints via Swagger UI and cURL", "done": False}
]

@app.get("/")
def read_root():
    return {
        "name": "Task API",
        "version": "1.0",
        "endpoints": ["/tasks"]
    }

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/tasks")
def get_all_tasks():
    return tasks_db

@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    for task in tasks_db:
        if task["id"] == task_id:
            return task
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"error": f"Task {task_id} not found"}
    )
