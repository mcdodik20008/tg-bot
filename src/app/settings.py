from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    bot_token: str = Field(alias="BOT_TOKEN")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    model_id: str = Field(default="Qwen/Qwen2-0.5B-Instruct", alias="MODEL_ID")
    llm_max_new_tokens: int = Field(default=256, alias="LLM_MAX_NEW_TOKENS")
    llm_temperature: float = Field(default=0.7, alias="LLM_TEMPERATURE")
    llm_top_p: float = Field(default=0.95, alias="LLM_TOP_P")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

settings = Settings()