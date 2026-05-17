# FastAPI — Complete Guide

## What is FastAPI?

FastAPI is a modern, fast (high-performance) web framework for building APIs with Python based on standard Python type hints. It is one of the fastest Python frameworks available, on par with NodeJS and Go.

Key features:
- **Fast**: Very high performance, on par with NodeJS and Go.
- **Fast to code**: Increase the speed to develop features by about 200% to 300%.
- **Fewer bugs**: Reduce about 40% of human-induced errors.
- **Intuitive**: Great editor support. Completion everywhere. Less time debugging.
- **Easy**: Designed to be easy to use and learn. Less time reading docs.
- **Short**: Minimize code duplication. Multiple features from each parameter declaration.
- **Robust**: Get production-ready code. With automatic interactive documentation.
- **Standards-based**: Based on (and fully compatible with) the open standards for APIs: OpenAPI and JSON Schema.

## Installation

```bash
pip install fastapi uvicorn[standard]
```

## First Steps — Hello World

Create a file `main.py`:

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}
```

Run the server:
```bash
uvicorn main:app --reload
```

- `main`: the file `main.py` (the Python "module").
- `app`: the object created inside of `main.py` with the line `app = FastAPI()`.
- `--reload`: make the server restart after code changes. Only use for development.

## Path Parameters

```python
@app.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id}
```

Path parameters with types are validated automatically. If you pass a non-integer, FastAPI returns a clear HTTP 422 error.

### Predefined values with Enum

```python
from enum import Enum
from fastapi import FastAPI

class ModelName(str, Enum):
    alexnet = "alexnet"
    resnet = "resnet"
    lenet = "lenet"

app = FastAPI()

@app.get("/models/{model_name}")
async def get_model(model_name: ModelName):
    if model_name is ModelName.alexnet:
        return {"model_name": model_name, "message": "Deep Learning FTW!"}
    return {"model_name": model_name}
```

## Query Parameters

```python
fake_items_db = [{"item_name": "Foo"}, {"item_name": "Bar"}]

@app.get("/items/")
async def read_item(skip: int = 0, limit: int = 10):
    return fake_items_db[skip : skip + limit]
```

URL: `http://127.0.0.1:8000/items/?skip=0&limit=10`

Optional query parameters:
```python
from typing import Optional

@app.get("/items/{item_id}")
async def read_item(item_id: str, q: Optional[str] = None):
    if q:
        return {"item_id": item_id, "q": q}
    return {"item_id": item_id}
```

## Request Body

Use Pydantic models to declare request bodies:

```python
from fastapi import FastAPI
from pydantic import BaseModel

class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None

app = FastAPI()

@app.post("/items/")
async def create_item(item: Item):
    return item
```

## Response Models

```python
from pydantic import BaseModel

class ItemIn(BaseModel):
    name: str
    price: float
    password: str

class ItemOut(BaseModel):
    name: str
    price: float

@app.post("/items/", response_model=ItemOut)
async def create_item(item: ItemIn):
    return item  # password is automatically excluded
```

## HTTP Status Codes

```python
from fastapi import FastAPI, status

@app.post("/items/", status_code=status.HTTP_201_CREATED)
async def create_item(name: str):
    return {"name": name}
```

Common status codes:
- `200` — OK (default for GET)
- `201` — Created (use for successful POST creating a resource)
- `204` — No Content (for DELETE)
- `404` — Not Found
- `422` — Unprocessable Entity (validation error)
- `500` — Internal Server Error

## Raising HTTP Exceptions

```python
from fastapi import FastAPI, HTTPException

items = {"foo": "The Foo Wrestlers"}

@app.get("/items/{item_id}")
async def read_item(item_id: str):
    if item_id not in items:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"item": items[item_id]}
```

## Dependency Injection

```python
from fastapi import Depends, FastAPI

async def common_parameters(q: str | None = None, skip: int = 0, limit: int = 100):
    return {"q": q, "skip": skip, "limit": limit}

@app.get("/items/")
async def read_items(commons: dict = Depends(common_parameters)):
    return commons
```

## Background Tasks

```python
from fastapi import BackgroundTasks

def write_notification(email: str, message=""):
    with open("log.txt", mode="w") as email_file:
        content = f"notification for {email}: {message}"
        email_file.write(content)

@app.post("/send-notification/{email}")
async def send_notification(email: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(write_notification, email, message="some notification")
    return {"message": "Notification sent in the background"}
```

## File Uploads

```python
from fastapi import FastAPI, File, UploadFile

@app.post("/files/")
async def create_file(file: bytes = File()):
    return {"file_size": len(file)}

@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile):
    return {"filename": file.filename}
```

## CORS Middleware

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://example.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Async vs Sync

FastAPI supports both async and sync path operation functions:

```python
@app.get("/async-endpoint/")
async def async_endpoint():
    # Use await inside async functions
    result = await some_async_operation()
    return result

@app.get("/sync-endpoint/")
def sync_endpoint():
    # Sync functions are run in a thread pool automatically
    result = some_blocking_operation()
    return result
```

Use `async def` when you use `await` inside. Otherwise, use regular `def`.
