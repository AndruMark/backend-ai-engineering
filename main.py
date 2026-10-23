from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

app = FastAPI(title="Task API", version="1.0")

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

@app.post("/tasks")
async def create_task(request: Request):
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "Invalid or missing JSON body"}
        )

    title = body.get("title") if isinstance(body, dict) else None
    if not title or not isinstance(title, str) or not title.strip():
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "Title is required and cannot be empty"}
        )

    next_id = max([t["id"] for t in tasks_db], default=0) + 1
    new_task = {
        "id": next_id,
        "title": title.strip(),
        "done": False
    }
    tasks_db.append(new_task)
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=new_task)
