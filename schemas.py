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
    visible: bool = True

class NoteUpdate(BaseModel):
    title: str = None
    description: str = None
    content: str = None
    tags: list = None
    terms: dict = None
    visible: bool = None

class NoteVisibilityUpdate(BaseModel):
    visible: bool
