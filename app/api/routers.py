from fastapi import APIRouter

from app.api.endpoints.user import router as user_router
from app.api.endpoints.task import router as task_router

main_router = APIRouter()

main_router.include_router(user_router)
main_router.include_router(task_router)