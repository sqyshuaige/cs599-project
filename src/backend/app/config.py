import os
from pydantic_settings import BaseSettings

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(os.path.dirname(BASE_DIR), "data")
os.makedirs(DATA_DIR, exist_ok=True)


class Settings(BaseSettings):
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DATABASE_URL: str = f"sqlite:///{os.path.join(DATA_DIR, 'oa.db')}"
    CHROMA_PERSIST_DIR: str = os.path.join(os.path.dirname(BASE_DIR), "chroma_db")

    model_config = {"env_file": os.path.join(BASE_DIR, ".env"), "env_file_encoding": "utf-8"}


settings = Settings()
