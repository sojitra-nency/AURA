from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "AURA API"
    debug: bool = False

    class Config:
        env_file = ".env"


settings = Settings()
