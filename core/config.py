import os
from pydantic import BaseSettings

class Settings(BaseSettings):
    WSDL_URL: str
    SERVICE_URL: str
    KONIK_USERNAME: str
    KONIK_PASWWORD: str

    class Config:
        env_file = ".env"

settings = Settings()