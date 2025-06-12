from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class TaskBase(BaseModel):
    name: str
    text_of_task: Optional[str] = None
    user_id: int
    created_at: Optional[datetime] = None
    close: Optional[datetime] = None


class TaskCreate(BaseModel):
    name: str
    text_of_task: Optional[str] = None
    created_at: Optional[str] = None


class Task(TaskBase):
    id: int

    class Config:
        from_attributes = True