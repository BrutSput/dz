from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.core.db import get_async_session
from app.core.user import current_user
from app.models.user import User
from app.schemas.task import Task, TaskCreate
from app.crud.task import crud_task

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.get(
    "/",
    response_model=List[Task],
    summary="Get tasks for the authenticated user",
)
async def get_user_tasks(
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_async_session),
):
    tasks = await crud_task.get_all_by_user_id(user_id=user.id, session=session)
    return tasks if tasks else []

@router.post(
    "/",
    response_model=Task,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new task for the authenticated user",
)
async def create_task(
    task_in: TaskCreate,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_async_session),
):
    # Set created_at to current UTC time
    created_at = datetime.utcnow()

    # Create task
    task = await crud_task.create(
        task_in=task_in,
        user_id=user.id,
        created_at=created_at,
        session=session
    )
    return task