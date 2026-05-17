# Pydantic v2 — Complete Guide

## What is Pydantic?

Pydantic is the most widely used data validation library for Python. It uses Python type annotations to define data schemas and validates data automatically. FastAPI uses Pydantic under the hood for request/response validation.

## Installation

```bash
pip install pydantic
```

## Basic Models

```python
from pydantic import BaseModel

class User(BaseModel):
    id: int
    name: str
    email: str
    age: int | None = None

user = User(id=1, name="Alice", email="alice@example.com")
print(user.model_dump())
# {'id': 1, 'name': 'Alice', 'email': 'alice@example.com', 'age': None}
```

## Field Validation

```python
from pydantic import BaseModel, Field, EmailStr

class User(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    age: int = Field(ge=0, le=150, description="Age in years")
    score: float = Field(default=0.0, ge=0.0, le=1.0)
```

Field constraints:
- `min_length`, `max_length` — for strings
- `ge` (>=), `le` (<=), `gt` (>), `lt` (<) — for numbers
- `pattern` — regex pattern for strings
- `default` — default value
- `description` — documentation string

## Nested Models

```python
from pydantic import BaseModel

class Address(BaseModel):
    street: str
    city: str
    country: str = "US"

class User(BaseModel):
    name: str
    address: Address

user = User(
    name="Alice",
    address={"street": "123 Main St", "city": "Anytown"}
)
print(user.address.city)  # Anytown
```

## Validators

```python
from pydantic import BaseModel, field_validator, model_validator

class UserModel(BaseModel):
    username: str
    password: str
    password_confirm: str

    @field_validator("username")
    @classmethod
    def username_must_be_alphanumeric(cls, v: str) -> str:
        if not v.isalnum():
            raise ValueError("Username must be alphanumeric")
        return v.lower()

    @model_validator(mode="after")
    def passwords_match(self) -> "UserModel":
        if self.password != self.password_confirm:
            raise ValueError("Passwords do not match")
        return self
```

## Type Annotations

Pydantic supports all common Python types:

```python
from typing import List, Dict, Optional, Union, Tuple
from pydantic import BaseModel

class ComplexModel(BaseModel):
    tags: List[str] = []
    metadata: Dict[str, str] = {}
    optional_field: Optional[str] = None
    mixed: Union[str, int]
    coordinates: Tuple[float, float]
```

## Serialization

```python
user = User(id=1, name="Alice", email="alice@example.com")

# To dict
user.model_dump()
user.model_dump(exclude={"password"})
user.model_dump(include={"name", "email"})

# To JSON string
user.model_dump_json()

# From dict
User.model_validate({"id": 1, "name": "Alice", "email": "a@b.com"})

# From JSON string
User.model_validate_json('{"id": 1, "name": "Alice", "email": "a@b.com"}')
```

## Model Config

```python
from pydantic import BaseModel, ConfigDict

class MyModel(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,    # strip whitespace from strings
        str_to_lower=True,            # convert strings to lowercase
        extra="forbid",               # error on extra fields
        frozen=True,                  # make model immutable
        populate_by_name=True,        # allow both alias and field name
    )
    name: str
```

## Aliases

```python
from pydantic import BaseModel, Field

class Item(BaseModel):
    item_name: str = Field(alias="itemName")
    item_price: float = Field(alias="itemPrice")

# Can create from alias
item = Item(itemName="Widget", itemPrice=9.99)
print(item.item_name)   # Widget

# Serialize with alias
item.model_dump(by_alias=True)  # {"itemName": "Widget", "itemPrice": 9.99}
```

## Computed Fields

```python
from pydantic import BaseModel, computed_field

class Rectangle(BaseModel):
    width: float
    height: float

    @computed_field
    @property
    def area(self) -> float:
        return self.width * self.height
```

## Generic Models

```python
from typing import Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")

class Response(BaseModel, Generic[T]):
    data: T
    status: str = "success"
    message: str = ""

class User(BaseModel):
    id: int
    name: str

response = Response[User](data=User(id=1, name="Alice"))
```

## Error Handling

```python
from pydantic import BaseModel, ValidationError

class User(BaseModel):
    id: int
    name: str

try:
    user = User(id="not-an-int", name=123)
except ValidationError as e:
    print(e.error_count())  # 2
    print(e.errors())
    # [
    #   {'type': 'int_parsing', 'loc': ('id',), 'msg': '...', ...},
    #   {'type': 'string_type', 'loc': ('name',), ...}
    # ]
```

## Pydantic Settings (for config/env vars)

```bash
pip install pydantic-settings
```

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "My App"
    api_key: str
    debug: bool = False
    
    model_config = ConfigDict(env_file=".env")

settings = Settings()
print(settings.api_key)  # reads from API_KEY env var
```
