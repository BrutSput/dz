from typing import Optional

from pydantic import EmailStr
from pydantic.v1 import BaseSettings


class Settings(BaseSettings):
    """все сосеться через .env"""
    app_title: str = 'Дз'
    description: str = 'ДЗ'
    database_url: str
    secret: str
    bot_tockn: str

    class Config:
        env_file = '.env'


settings = Settings()
