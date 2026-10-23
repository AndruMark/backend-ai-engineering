from fastapi import FastAPI, Request, Response, status
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

@app.put("/tasks/{task_id}")
async def update_task(task_id: int, request: Request):
    target_task = None
    for task in tasks_db:
        if task["id"] == task_id:
            target_task = task
            break

    if target_task is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": f"Task {task_id} not found"}
        )

    try:
        body = await request.json()
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "Invalid or missing JSON body"}
        )

    if not isinstance(body, dict) or ("title" not in body and "done" not in body):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "Request body must include 'title' or 'done'"}
        )

    if "title" in body:
        title_val = body["title"]
        if not isinstance(title_val, str) or not title_val.strip():
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "Title cannot be empty"}
            )
        target_task["title"] = title_val.strip()

    if "done" in body:
        done_val = body["done"]
        if not isinstance(done_val, bool):
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "Field 'done' must be a boolean"}
            )
        target_task["done"] = done_val

    return JSONResponse(status_code=status.HTTP_200_OK, content=target_task)

@app.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    for index, task in enumerate(tasks_db):
        if task["id"] == task_id:
            tasks_db.pop(index)
            return Response(status_code=status.HTTP_204_NO_CONTENT)

    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"error": f"Task {task_id} not found"}
    )
