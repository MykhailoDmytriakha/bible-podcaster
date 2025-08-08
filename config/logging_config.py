"""
Logging configuration for Bible Podcaster project.
"""
import logging
import logging.config
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import json

from .config import settings


class StructuredFormatter(logging.Formatter):
    """Custom formatter that outputs structured JSON logs."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add exception information if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields from record
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'exc_info', 'exc_text', 'stack_info',
                          'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                          'thread', 'threadName', 'processName', 'process', 'message']:
                log_data[key] = value
        
        return json.dumps(log_data, ensure_ascii=False)


class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output."""
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors."""
        # Get color for level
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        
        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        
        # Format message
        message = f"{color}[{timestamp}] {record.levelname:<8} {record.name}: {record.getMessage()}{reset}"
        
        # Add exception information if present
        if record.exc_info:
            message += f"\n{self.formatException(record.exc_info)}"
        
        return message


def setup_logging(
    log_level: Optional[str] = None,
    log_format: Optional[str] = None,
    enable_console: bool = True,
    enable_file: bool = True,
    enable_json: bool = False,
    log_file: Optional[str] = None
) -> None:
    """
    Setup logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Log format string
        enable_console: Enable console logging
        enable_file: Enable file logging
        enable_json: Enable JSON structured logging
        log_file: Custom log file path
    """
    app_settings = settings
    
    # Use settings defaults if not provided
    if log_level is None:
        log_level = app_settings.log_level.value
    if log_format is None:
        log_format = app_settings.log_format
    if log_file is None:
        log_file = app_settings.get_absolute_path(app_settings.logs_dir) / "bible_podcaster.log"
    
    # Ensure logs directory exists
    app_settings.create_directories()
    
    # Configure logging
    config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': log_format,
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'colored': {
                '()': ColoredFormatter,
                'format': log_format,
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'json': {
                '()': StructuredFormatter
            }
        },
        'handlers': {},
        'loggers': {
            '': {  # Root logger
                'handlers': [],
                'level': log_level,
                'propagate': False
            },
            'bible_podcaster': {
                'handlers': [],
                'level': log_level,
                'propagate': False
            }
        }
    }
    
    handlers = []
    
    # Console handler
    if enable_console:
        console_handler = {
            'class': 'logging.StreamHandler',
            'level': log_level,
            'formatter': 'colored' if sys.stdout.isatty() else 'standard',
            'stream': 'ext://sys.stdout'
        }
        config['handlers']['console'] = console_handler
        handlers.append('console')
    
    # File handler
    if enable_file:
        file_handler = {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': log_level,
            'formatter': 'json' if enable_json else 'standard',
            'filename': str(log_file),
            'maxBytes': 10 * 1024 * 1024,  # 10MB
            'backupCount': 5,
            'encoding': 'utf-8'
        }
        config['handlers']['file'] = file_handler
        handlers.append('file')
    
    # Error file handler
    if enable_file:
        error_file = str(log_file).replace('.log', '_errors.log')
        error_handler = {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'ERROR',
            'formatter': 'json' if enable_json else 'standard',
            'filename': error_file,
            'maxBytes': 10 * 1024 * 1024,  # 10MB
            'backupCount': 5,
            'encoding': 'utf-8'
        }
        config['handlers']['error_file'] = error_handler
        handlers.append('error_file')
    
    # Assign handlers to loggers
    config['loggers']['']['handlers'] = handlers
    config['loggers']['bible_podcaster']['handlers'] = handlers
    
    # Apply configuration
    logging.config.dictConfig(config)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return logging.getLogger(f"bible_podcaster.{name}")


def log_function_call(func_name: str, **kwargs):
    """
    Log function call with parameters.
    
    Args:
        func_name: Function name
        **kwargs: Function parameters
    """
    logger = get_logger("function_calls")
    logger.debug(f"Calling {func_name}", extra={'function': func_name, 'parameters': kwargs})


def log_pipeline_step(step_name: str, status: str, **kwargs):
    """
    Log pipeline step execution.
    
    Args:
        step_name: Step name
        status: Step status (started, completed, failed)
        **kwargs: Additional step information
    """
    logger = get_logger("pipeline")
    logger.info(f"Pipeline step {step_name}: {status}", 
                extra={'step': step_name, 'status': status, **kwargs})


def log_api_call(service: str, endpoint: str, response_time: float, status_code: int = None):
    """
    Log API call information.
    
    Args:
        service: Service name (e.g., 'openai', 'elevenlabs')
        endpoint: API endpoint
        response_time: Response time in seconds
        status_code: HTTP status code
    """
    logger = get_logger("api_calls")
    logger.info(f"API call to {service}/{endpoint}", 
                extra={
                    'service': service,
                    'endpoint': endpoint,
                    'response_time': response_time,
                    'status_code': status_code
                })


def log_error(error: Exception, context: Dict[str, Any] = None):
    """
    Log error with context information.
    
    Args:
        error: Exception object
        context: Additional context information
    """
    logger = get_logger("errors")
    logger.error(f"Error occurred: {str(error)}", 
                 extra={'error_type': type(error).__name__, 'context': context or {}},
                 exc_info=True)


def log_performance(operation: str, duration: float, **kwargs):
    """
    Log performance metrics.
    
    Args:
        operation: Operation name
        duration: Operation duration in seconds
        **kwargs: Additional performance metrics
    """
    logger = get_logger("performance")
    logger.info(f"Performance: {operation} took {duration:.2f}s", 
                extra={'operation': operation, 'duration': duration, **kwargs})


# Context manager for logging function execution
class LoggedFunction:
    """Context manager for logging function execution."""
    
    def __init__(self, func_name: str, logger: logging.Logger = None):
        self.func_name = func_name
        self.logger = logger or get_logger("function_execution")
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.debug(f"Starting {self.func_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (datetime.now() - self.start_time).total_seconds()
        if exc_type:
            self.logger.error(f"{self.func_name} failed after {duration:.2f}s", 
                             exc_info=(exc_type, exc_val, exc_tb))
        else:
            self.logger.debug(f"{self.func_name} completed in {duration:.2f}s")


# Initialize logging when module is imported
if __name__ != "__main__":
    setup_logging()


if __name__ == "__main__":
    # Example usage
    setup_logging(log_level="DEBUG", enable_json=True)
    
    logger = get_logger("example")
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    
    # Test structured logging
    log_function_call("test_function", param1="value1", param2=42)
    log_pipeline_step("text_processing", "started", input_length=1000)
    log_api_call("openai", "completions", 1.5, 200)
    log_performance("text_generation", 2.3, tokens=150) 