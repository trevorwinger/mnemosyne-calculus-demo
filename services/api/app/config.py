from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "postgresql+psycopg://office_hours:change-me-before-production@db:5432/office_hours"
    app_env: str = "development"
    demo_mode: bool = False
    student_only_mode: bool = True
    web_origin: str = "http://localhost:3000"
    ollama_base_url: str = "http://host.docker.internal:11434"
    max_upload_mb: int = 25
    max_request_mb: int = 26
    upload_dir: str = "/app/uploads"
    chat_log_dir: str = "/app/chats"
    chat_logging_enabled: bool = True
    max_context_chars: int = 18000
    max_model_concurrency: int = 1
    ollama_timeout_seconds: int = 60
    request_limit_per_window: int = 120
    request_limit_window_seconds: int = 60
    code_execution_enabled: bool = False
    code_runner_socket: str = "/runner/java-runner.sock"
    code_execution_timeout_seconds: int = 10
    apex_textbook_path: str = "/seed/apex-novideo.pdf"
    prototype_default_model: str = "demo-tutor"

settings = Settings()
