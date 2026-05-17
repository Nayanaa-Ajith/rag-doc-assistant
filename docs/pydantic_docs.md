# Pydantic v2 — Complete Reference

## What is Pydantic?

Pydantic is the most widely used data validation library for Python. It uses Python type annotations to define data schemas, validate input, and serialize/deserialize data. FastAPI is built on top of Pydantic.

Pydantic v2 was rewritten in Rust, making it 5–50x faster than v1.

## Installation

```bash
pip install pydantic
```

## Defining Models

```python
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class User(BaseModel):
    id: int
    name: str
    email: str
    age: Optional[int] = None
    created_at: datetime = datetime.utcnow()
```

## Creating Instances

```python
user = User(id=1, name="John", email="john@example.com", age=30)
print(user.name)       # John
print(user.model_dump()) # {'id': 1, 'name': 'John', ...}
print(user.model_json()) # JSON string
```

## Field Validators

### Field-level validation with `@field_validator`

```python
from pydantic import BaseModel, field_validator

class UserModel(BaseModel):
    name: str
    email: str
    age: int

    @field_validator('name')
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('Name cannot be empty')
        return v.title()  # normalize to title case

    @field_validator('age')
    @classmethod
    def age_must_be_positive(cls, v: int) -> int:
        if v < 0:
            raise ValueError('Age must be non-negative')
        return v

    @field_validator('email')
    @classmethod
    def email_must_be_valid(cls, v: str) -> str:
        if '@' not in v:
            raise ValueError('Invalid email format')
        return v.lower()
```

### Model-level validation with `@model_validator`

```python
from pydantic import BaseModel, model_validator

class PasswordModel(BaseModel):
    password: str
    confirm_password: str

    @model_validator(mode='after')
    def passwords_match(self) -> 'PasswordModel':
        if self.password != self.confirm_password:
            raise ValueError('Passwords do not match')
        return self
```

## Field Configuration

Use `Field()` for additional constraints and metadata:

```python
from pydantic import BaseModel, Field

class Product(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Product name")
    price: float = Field(..., gt=0, description="Must be positive")
    discount: float = Field(default=0.0, ge=0, le=1.0, description="0 to 1")
    tags: list[str] = Field(default_factory=list)
    sku: str = Field(..., pattern=r'^[A-Z]{3}-\d{4}$', examples=["ABC-1234"])
```

## Nested Models

```python
class Address(BaseModel):
    street: str
    city: str
    country: str = "India"

class Person(BaseModel):
    name: str
    address: Address
    friends: list['Person'] = []  # self-referential

# Usage
person = Person(
    name="Alice",
    address={"street": "123 Main St", "city": "Mumbai"}
)
```

## Type Coercion

Pydantic automatically converts types when possible:

```python
class Flexible(BaseModel):
    value: int

f = Flexible(value="42")  # "42" → 42 automatically
f = Flexible(value=3.7)   # 3.7 → 3 (truncated)
```

Use `model_config = ConfigDict(strict=True)` to disable coercion.

## Model Configuration

```python
from pydantic import BaseModel, ConfigDict

class StrictModel(BaseModel):
    model_config = ConfigDict(
        strict=True,               # no type coercion
        str_strip_whitespace=True, # auto-strip strings
        validate_default=True,     # validate even default values
        frozen=True,               # immutable (hash-able)
        populate_by_name=True,     # allow both alias and field name
    )
    name: str
```

## Aliases

Map external JSON field names to Python attribute names:

```python
from pydantic import BaseModel, Field

class APIResponse(BaseModel):
    user_id: int = Field(alias="userId")
    first_name: str = Field(alias="firstName")
    last_name: str = Field(alias="lastName")

# Parsing camelCase JSON
data = {"userId": 1, "firstName": "John", "lastName": "Doe"}
resp = APIResponse.model_validate(data)
print(resp.user_id)  # 1
```

## Serialization

```python
user = User(id=1, name="Alice", email="alice@example.com")

# To dict
d = user.model_dump()
# Exclude None values
d = user.model_dump(exclude_none=True)
# Include only specific fields
d = user.model_dump(include={"name", "email"})
# Exclude fields
d = user.model_dump(exclude={"id"})
# Use aliases in output
d = user.model_dump(by_alias=True)

# To JSON string
json_str = user.model_dump_json()
json_str = user.model_dump_json(indent=2)
```

## Parsing / Deserialization

```python
# From dict
user = User.model_validate({"id": 1, "name": "Alice", "email": "a@b.com"})

# From JSON string
user = User.model_validate_json('{"id": 1, "name": "Alice", "email": "a@b.com"}')

# From ORM model (SQLAlchemy etc.)
class Config:
    from_attributes = True
user = User.model_validate(orm_user)
```

## Union Types / Discriminated Unions

```python
from typing import Union, Literal
from pydantic import BaseModel

class Cat(BaseModel):
    type: Literal["cat"]
    meow_volume: int

class Dog(BaseModel):
    type: Literal["dog"]
    bark_frequency: int

class Pet(BaseModel):
    animal: Union[Cat, Dog]  # pydantic picks based on 'type' field
```

## Generic Models

```python
from pydantic import BaseModel
from typing import Generic, TypeVar

T = TypeVar('T')

class Response(BaseModel, Generic[T]):
    data: T
    message: str
    success: bool = True

# Usage
response = Response[User](data=user, message="Found")
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

## JSON Schema Generation

```python
import json
schema = User.model_json_schema()
print(json.dumps(schema, indent=2))
```

## Error Handling

```python
from pydantic import ValidationError

try:
    user = User(id="not-an-int", name="", email="invalid")
except ValidationError as e:
    print(e.error_count())  # number of errors
    for error in e.errors():
        print(f"Field: {error['loc']}, Error: {error['msg']}")
```

## Custom Types

```python
from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema

class PositiveInt:
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler: GetCoreSchemaHandler):
        return core_schema.int_schema(gt=0)

class MyModel(BaseModel):
    count: PositiveInt
```

## Integration with FastAPI

Pydantic models are used directly as FastAPI request/response bodies. FastAPI automatically generates OpenAPI docs from Pydantic schemas, validates incoming requests, and serializes responses.

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str
    price: float

@app.post("/items/", response_model=Item)
async def create_item(item: Item) -> Item:
    return item
```
