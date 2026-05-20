from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Environment
    environment: str = "development"
    
    # Database
    database_url: str = "postgresql://user:password@localhost:5432/hkaic"
    
    # Supabase
    supabase_url: str = ""
    supabase_key: str = ""
    supabase_service_role_key: str = ""
    
    # OpenAI
    openai_api_key: str = ""
    
    # Security
    secret_key: str = "your-secret-key-here-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # File Upload
    upload_dir: str = "./uploads"
    max_upload_size: int = 10485760  # 10MB
    
    # CORS
    allowed_origins: str = "http://localhost:3000,http://localhost:8000"
    
    @property
    def allowed_origins_list(self) -> List[str]:
        return self.allowed_origins.split(",")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
