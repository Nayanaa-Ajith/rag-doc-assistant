# FastAPI — Official Documentation Reference

## What is FastAPI?

FastAPI is a modern, fast (high-performance), web framework for building APIs with Python 3.8+ based on standard Python type hints. It is one of the fastest Python frameworks available, on par with NodeJS and Go, thanks to Starlette and Pydantic underneath.

FastAPI is based on OpenAPI (formerly Swagger) and JSON Schema standards. It generates interactive API documentation automatically.

## Key Features

- **Fast**: Very high performance, on par with NodeJS and Go.
- **Fast to code**: Increases development speed significantly.
- **Fewer bugs**: Reduces human-induced errors by about 40%.
- **Intuitive**: Great editor support, completion everywhere, less time debugging.
- **Easy**: Designed to be easy to use and learn.
- **Short**: Minimize code duplication.
- **Robust**: Get production-ready code with automatic interactive documentation.
- **Standards-based**: Based on OpenAPI and JSON Schema.

## Installation

```bash
pip install fastapi uvicorn[standard]
```

## Creating Your First App

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}
```

Run with:
```bash
uvicorn main:app --reload
```

## Path Parameters

Path parameters are captured from the URL path.

```python
@app.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id}
```

FastAPI automatically validates types. If you pass a string where an int is expected, it returns a proper HTTP error.

## Query Parameters

Any parameter not in the path is treated as a query parameter.

```python
@app.get("/items/")
async def read_items(skip: int = 0, limit: int = 10):
    return fake_items_db[skip : skip + limit]
```

Optional query parameters use `Optional[str] = None`.

## Request Body

Use Pydantic models for request bodies:

```python
from pydantic import BaseModel

class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None

@app.post("/items/")
async def create_item(item: Item):
    return item
```

FastAPI automatically:
- Reads the request body as JSON
- Converts types
- Validates data
- Documents the schema

## Dependency Injection

FastAPI has a powerful Dependency Injection system. Dependencies are declared using `Depends()`.

```python
from fastapi import Depends, FastAPI

async def common_parameters(q: str | None = None, skip: int = 0, limit: int = 100):
    return {"q": q, "skip": skip, "limit": limit}

@app.get("/items/")
async def read_items(commons: dict = Depends(common_parameters)):
    return commons
```

Dependencies can themselves have dependencies (sub-dependencies), creating powerful composable patterns.

## Authentication with OAuth2

FastAPI supports OAuth2 with Password flow:

```python
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import Depends

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect credentials")
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me")
async def read_users_me(token: str = Depends(oauth2_scheme)):
    return decode_token(token)
```

## JWT Authentication

For JWT tokens, use the `python-jose` library:

```python
from jose import JWTError, jwt
from datetime import datetime, timedelta

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
```

## Background Tasks

FastAPI supports background tasks that run after returning a response:

```python
from fastapi import BackgroundTasks

def write_notification(email: str, message=""):
    with open("log.txt", mode="w") as f:
        f.write(f"notification for {email}: {message}")

@app.post("/send-notification/{email}")
async def send_notification(email: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(write_notification, email, message="some notification")
    return {"message": "Notification sent in the background"}
```

## Middleware

Middleware processes every request and response:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Exception Handling

Custom exception handlers:

```python
from fastapi import Request
from fastapi.responses import JSONResponse

class UnicornException(Exception):
    def __init__(self, name: str):
        self.name = name

@app.exception_handler(UnicornException)
async def unicorn_exception_handler(request: Request, exc: UnicornException):
    return JSONResponse(
        status_code=418,
        content={"message": f"Oops! {exc.name} did something wrong."},
    )
```

## File Uploads

```python
from fastapi import UploadFile, File

@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile):
    return {"filename": file.filename, "content_type": file.content_type}
```

Multiple files:
```python
@app.post("/uploadfiles/")
async def create_upload_files(files: list[UploadFile]):
    return {"filenames": [file.filename for file in files]}
```

## Response Models

Control what gets returned using `response_model`:

```python
class UserIn(BaseModel):
    username: str
    password: str
    email: str

class UserOut(BaseModel):
    username: str
    email: str

@app.post("/user/", response_model=UserOut)
async def create_user(user: UserIn):
    return user   # password is automatically excluded!
```

## HTTP Status Codes

```python
from fastapi import status

@app.post("/items/", status_code=status.HTTP_201_CREATED)
async def create_item(name: str):
    return {"name": name}
```

## Routers (APIRouter)

Organize routes into separate files:

```python
# routers/items.py
from fastapi import APIRouter
router = APIRouter(prefix="/items", tags=["items"])

@router.get("/")
async def read_items():
    return [{"name": "Item Foo"}, {"name": "Item Bar"}]

# main.py
from routers import items
app.include_router(items.router)
```

## Testing FastAPI

```python
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}
```
