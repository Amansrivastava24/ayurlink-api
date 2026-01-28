from pydantic_settings import BaseSettings, SettingsConfigDict
import os

# Construct the path to the .env file in the project's root directory
env_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env")

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=env_path, env_file_encoding="utf-8")
    
    DATABASE_URL: str
    WHO_CLIENT_ID: str
    WHO_CLIENT_SECRET: str

settings = Settings()