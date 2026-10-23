# Backend AI Engineering

Production-ready backend services, foundational API architectures, and intelligent workflows built with Python and FastAPI.

## Repository Overview
This repository contains progressive backend engineering modules:
- **`BE-01`**: Foundations — In-Memory RESTful CRUD API with strict HTTP status code compliance, Pydantic v2 data validation, and interactive OpenAPI documentation.
- *(Upcoming Modules)*: Relational & Vector database persistence (PostgreSQL / pgvector), asynchronous task queues, and LLM agent tool interfaces.

---

## Module: BE-01 — Task Management CRUD API

### Architecture & Tech Stack
- **Framework:** FastAPI
- **Data Validation & Serialization:** Pydantic v2
- **ASGI Server:** Uvicorn
- **Storage:** In-Memory List (Transient State)

### Getting Started

#### 1. Setup Environment
```powershell
git clone https://github.com/<YOUR_GITHUB_USERNAME>/backend-ai-engineering.git
cd backend-ai-engineering
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

#### 2. Run the Server
```powershell
uvicorn main:app --reload --port 8000
```

### Endpoints Specification

| HTTP Method | Endpoint | Description | Status Code |
| :--- | :--- | :--- | :--- |
| `GET` | `/` | API Root Metadata | `200 OK` |
| `GET` | `/health` | Server Health Check probe | `200 OK` |
| `GET` | `/tasks` | List all tasks | `200 OK` |
| `GET` | `/tasks/{id}` | Retrieve single task by ID | `200 OK` / `404 Not Found` |
| `POST` | `/tasks` | Create task with body validation | `201 Created` / `400 Bad Request` |
| `PUT` | `/tasks/{id}` | Update task title or status | `200 OK` / `400 Bad Request` / `404 Not Found` |
| `DELETE` | `/tasks/{id}` | Remove task | `204 No Content` / `404 Not Found` |

### Verified cURL Sample

```bash
$ curl -i -X POST http://localhost:8000/tasks \
    -H "Content-Type: application/json" \
    -d '{"title":"Buy milk"}'

HTTP/1.1 201 Created
server: uvicorn
content-length: 37
content-type: application/json

{"id":4,"title":"Buy milk","done":false}
```

### Interactive API Documentation
Interactive OpenAPI documentation and execution UI is available at `http://localhost:8000/docs`.

![Swagger UI](swagger_ui_screenshot.png)
