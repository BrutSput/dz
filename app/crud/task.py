from datetime import datetime
from typing import List, Optional
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.task import Task
from app.schemas.task import TaskCreate


class CRUDBase:
    def __init__(self, model):
        self.model = model

    async def get_by_id(self, user_id: int, session: AsyncSession):
        db_objects = await session.execute(
            select(self.model).where(self.model.user_id == user_id)
        )
        return db_objects.scalars().first()

    async def get_all_by_user_id(self, user_id: int, session: AsyncSession) -> List:
        db_objects = await session.execute(
            select(self.model).where(self.model.user_id == user_id).order_by(desc(self.model.created_at))
        )
        return db_objects.scalars().all()

    async def create(self, task_in: TaskCreate, user_id: int, created_at: datetime, session: AsyncSession) -> Task:
        db_task = self.model(
            name=task_in.name,
            text_of_task=task_in.text_of_task,
            user_id=user_id,
            created_at=created_at
        )
        session.add(db_task)
        await session.commit()
        await session.refresh(db_task)
        return db_task


crud_task = CRUDBase(Task)