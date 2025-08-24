from pydantic_settings import BaseSettings
class Object(BaseSettings):
    port: int = 8080
    api_link : str
    key : str
    class Config:
        env_file = ".env"

settings = Object()