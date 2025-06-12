from fastapi import FastAPI

from app.core.config import settings
from app.api.routers import main_router
from app.view.user import router as auth_view_router

app = FastAPI(title=settings.app_title)
app.include_router(main_router)
app.include_router(auth_view_router)