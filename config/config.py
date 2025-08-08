"""
Configuration management for Bible Podcaster project.
"""
import os
from pathlib import Path
from typing import Optional, List
from pydantic import Field, validator
from pydantic_settings import BaseSettings
from enum import Enum


class Environment(str, Enum):
    """Application environments."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class LogLevel(str, Enum):
    """Log levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class AppSettings(BaseSettings):
    """Application settings."""
    
    # Environment
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = Field(default=True, description="Enable debug mode")
    
    # Project paths
    project_root: Path = Field(default_factory=lambda: Path(__file__).parent.parent)
    data_dir: Path = Field(default_factory=lambda: Path("data"))
    output_dir: Path = Field(default_factory=lambda: Path("output"))
    logs_dir: Path = Field(default_factory=lambda: Path("logs"))
    
    # API Keys
    openai_api_key: Optional[str] = Field(None, description="OpenAI API key")
    openai_api_model: str = Field("gpt-4o-mini", description="OpenAI model to use")
    anthropic_api_key: Optional[str] = Field(None, description="Anthropic API key")
    elevenlabs_api_key: Optional[str] = Field(None, description="Eleven Labs API key")
    youtube_api_key: Optional[str] = Field(None, description="YouTube API key")
    
    # YouTube OAuth
    youtube_client_id: Optional[str] = Field(None, description="YouTube OAuth client ID")
    youtube_client_secret: Optional[str] = Field(None, description="YouTube OAuth client secret")
    
    # Audio settings
    audio_sample_rate: int = Field(22050, description="Audio sample rate")
    audio_format: str = Field("mp3", description="Audio output format")
    audio_quality: str = Field("high", description="Audio quality setting")
    
    # Video settings
    video_resolution: str = Field("1920x1080", description="Video resolution")
    video_fps: int = Field(30, description="Video frames per second")
    video_format: str = Field("mp4", description="Video output format")
    
    # Image settings
    image_width: int = Field(1920, description="Image width")
    image_height: int = Field(1080, description="Image height")
    image_format: str = Field("png", description="Image format")
    
    # Text processing
    max_text_length: int = Field(10000, description="Maximum text length for processing")
    min_text_length: int = Field(100, description="Minimum text length for processing")
    
    # Logging
    log_level: LogLevel = LogLevel.INFO
    log_format: str = Field(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format string"
    )
    
    # Pipeline settings
    pipeline_timeout: int = Field(3600, description="Pipeline timeout in seconds")
    retry_attempts: int = Field(3, description="Number of retry attempts")
    pipeline_text_processing_enabled: bool = Field(True, description="Enable text processing stage")
    pipeline_audio_generation_enabled: bool = Field(True, description="Enable audio generation stage")
    pipeline_image_generation_enabled: bool = Field(True, description="Enable image generation stage")
    pipeline_video_creation_enabled: bool = Field(True, description="Enable video creation stage")
    pipeline_youtube_upload_enabled: bool = Field(False, description="Enable YouTube upload stage")
    pipeline_max_workers: int = Field(4, description="Max workers for parallel tasks (reserved)")
    pipeline_keep_intermediate_files: bool = Field(False, description="Keep intermediate files after success")
    
    # YouTube OAuth files
    youtube_credentials_path: Optional[Path] = Field(None, description="Path to YouTube OAuth client_secret.json")
    youtube_token_path: Optional[Path] = Field(None, description="Path to store OAuth token.json")

    # Web interface (optional)
    web_host: str = Field("localhost", description="Web interface host")
    web_port: int = Field(8000, description="Web interface port")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        
    @validator("project_root", pre=True)
    def validate_project_root(cls, v):
        if isinstance(v, str):
            return Path(v)
        return v
    
    @validator("data_dir", "output_dir", "logs_dir", pre=True)
    def validate_directories(cls, v):
        if isinstance(v, str):
            return Path(v)
        return v
    
    def create_directories(self):
        """Create necessary directories if they don't exist."""
        directories = [
            self.project_root / self.data_dir,
            self.project_root / self.output_dir,
            self.project_root / self.logs_dir,
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def get_absolute_path(self, relative_path: Path) -> Path:
        """Get absolute path relative to project root."""
        if relative_path.is_absolute():
            return relative_path
        return self.project_root / relative_path
    
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == Environment.PRODUCTION
    
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == Environment.DEVELOPMENT


# Global settings instance
settings = AppSettings()


if __name__ == "__main__":
    # Example usage
    print("Application Settings:")
    print(f"Environment: {settings.environment}")
    print(f"Debug: {settings.debug}")
    print(f"Project Root: {settings.project_root}")
    print(f"Log Level: {settings.log_level}")
    
    print("\nPipeline Settings:")
    print(f"Max Workers: {pipeline_settings.max_workers}")
    print(f"Keep Intermediate Files: {pipeline_settings.keep_intermediate_files}") 