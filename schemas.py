from pydantic import BaseModel
from typing import Optional

class UserCreate(BaseModel):
    login: str
    password: str
    type: str = "none"

class UserUpdate(BaseModel):
    login: Optional[str] = None
    password: Optional[str] = None
    type: Optional[str] = None

class UserLogin(BaseModel):
    login: str
    password: str

class NoteCreate(BaseModel):
    title: str
    description: str
    content: str
    tags: list
    terms: dict
    locked: bool = False
    visibility: str = "public"

class NoteUpdate(BaseModel):
    title: str = None
    description: str = None
    content: str = None
    tags: list = None
    terms: dict = None
    locked: bool = None
    visibility: str = None

class NoteVisibilityUpdate(BaseModel):
    visibility: str
    locked: bool = None
