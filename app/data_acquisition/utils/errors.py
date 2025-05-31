"""
Error handling and logging utilities for the data acquisition system
"""

import logging
import traceback
from typing import Optional, Dict, Any
from datetime import datetime
from pathlib import Path
from enum import Enum

class ErrorCode(Enum):
    """Standard error codes for data acquisition"""
    UNKNOWN = "UNKNOWN"
    NETWORK_ERROR = "NETWORK_ERROR"
    API_KEY_MISSING = "API_KEY_MISSING"
    API_RATE_LIMIT = "API_RATE_LIMIT"
    INVALID_COORDINATES = "INVALID_COORDINATES"
    DATA_NOT_AVAILABLE = "DATA_NOT_AVAILABLE"
    FILE_SIZE_EXCEEDED = "FILE_SIZE_EXCEEDED"
    CACHE_ERROR = "CACHE_ERROR"
    PROCESSING_ERROR = "PROCESSING_ERROR"
    COORDINATE_CONVERSION_ERROR = "COORDINATE_CONVERSION_ERROR"
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"

class DataAcquisitionError(Exception):
    """Base exception for data acquisition errors"""
    
    def __init__(
        self, 
        message: str, 
        error_code: ErrorCode = ErrorCode.UNKNOWN,
        details: Optional[Dict[str, Any]] = None,
        source: Optional[str] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.source = source
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for API responses"""
        return {
            "error_code": self.error_code.value,
            "message": self.message,
            "source": self.source,
            "details": self.details,
            "timestamp": self.timestamp.isoformat()
        }

class NetworkError(DataAcquisitionError):
    """Network-related errors"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, ErrorCode.NETWORK_ERROR, **kwargs)

class APIKeyError(DataAcquisitionError):
    """API key related errors"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, ErrorCode.API_KEY_MISSING, **kwargs)

class RateLimitError(DataAcquisitionError):
    """Rate limit exceeded errors"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, ErrorCode.API_RATE_LIMIT, **kwargs)

class CoordinateError(DataAcquisitionError):
    """Coordinate validation errors"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, ErrorCode.INVALID_COORDINATES, **kwargs)

class DataNotAvailableError(DataAcquisitionError):
    """Data not available errors"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, ErrorCode.DATA_NOT_AVAILABLE, **kwargs)

class FileSizeError(DataAcquisitionError):
    """File size exceeded errors"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, ErrorCode.FILE_SIZE_EXCEEDED, **kwargs)

def setup_logging(log_dir: str = "logs", log_level: str = "INFO") -> logging.Logger:
    """Setup logging for the data acquisition system"""
    
    # Create log directory
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    # Configure logging
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # File handler
    file_handler = logging.FileHandler(
        log_path / "data_acquisition.log",
        encoding="utf-8"
    )
    file_handler.setLevel(getattr(logging, log_level.upper()))
    file_handler.setFormatter(logging.Formatter(log_format))
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(log_format))
    
    # Setup logger
    logger = logging.getLogger("data_acquisition")
    logger.setLevel(getattr(logging, log_level.upper()))
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def log_error(
    logger: logging.Logger, 
    error: Exception, 
    context: str = "",
    extra_data: Optional[Dict[str, Any]] = None
):
    """Log an error with context and traceback"""
    
    error_msg = f"{context}: {str(error)}" if context else str(error)
    
    if isinstance(error, DataAcquisitionError):
        logger.error(
            f"[{error.error_code.value}] {error_msg}",
            extra={"error_details": error.details, "extra_data": extra_data}
        )
    else:
        logger.error(error_msg, extra={"extra_data": extra_data})
    
    # Log traceback for unexpected errors
    if not isinstance(error, DataAcquisitionError):
        logger.debug(f"Traceback: {traceback.format_exc()}")

def log_acquisition_attempt(
    logger: logging.Logger,
    source: str,
    lat: float,
    lng: float,
    buffer_km: float,
    data_types: Optional[list] = None
):
    """Log a data acquisition attempt"""
    logger.info(
        f"Starting data acquisition: source={source}, "
        f"coords=({lat}, {lng}), buffer={buffer_km}km, "
        f"types={data_types or 'all'}"
    )

def log_acquisition_success(
    logger: logging.Logger,
    source: str,
    files: Dict[str, str],
    processing_time: float,
    download_size_mb: float
):
    """Log successful data acquisition"""
    logger.info(
        f"Data acquisition successful: source={source}, "
        f"files={len(files)}, time={processing_time:.1f}s, "
        f"size={download_size_mb:.1f}MB"
    )

def handle_api_error(error: Exception, source: str) -> DataAcquisitionError:
    """Convert generic API errors to DataAcquisitionError"""
    
    error_msg = str(error).lower()
    
    if "api key" in error_msg or "unauthorized" in error_msg:
        return APIKeyError(
            f"API key required or invalid for {source}",
            source=source,
            details={"original_error": str(error)}
        )
    elif "rate limit" in error_msg or "too many requests" in error_msg:
        return RateLimitError(
            f"Rate limit exceeded for {source}",
            source=source,
            details={"original_error": str(error)}
        )
    elif "network" in error_msg or "connection" in error_msg:
        return NetworkError(
            f"Network error accessing {source}",
            source=source,
            details={"original_error": str(error)}
        )
    else:
        return DataAcquisitionError(
            f"Error accessing {source}: {error}",
            source=source,
            details={"original_error": str(error)}
        )

def retry_with_exponential_backoff(
    func,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: tuple = (Exception,)
):
    """Decorator for retrying functions with exponential backoff"""
    
    def decorator(f):
        async def wrapper(*args, **kwargs):
            import asyncio
            
            for attempt in range(max_retries + 1):
                try:
                    return await f(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_retries:
                        raise e
                    
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    await asyncio.sleep(delay)
            
        return wrapper
    return decorator

class ErrorTracker:
    """Track and analyze errors for system health monitoring"""
    
    def __init__(self):
        self.errors = []
        self.error_counts = {}
    
    def record_error(self, error: DataAcquisitionError):
        """Record an error for tracking"""
        self.errors.append(error)
        
        error_key = f"{error.source}:{error.error_code.value}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of recent errors"""
        recent_errors = [
            e for e in self.errors 
            if (datetime.now() - e.timestamp).days < 1
        ]
        
        return {
            "total_errors_24h": len(recent_errors),
            "error_by_code": {},
            "error_by_source": {},
            "most_common_errors": []
        }
    
    def clear_old_errors(self, days: int = 7):
        """Clear errors older than specified days"""
        cutoff = datetime.now()
        cutoff = cutoff.replace(day=cutoff.day - days)
        
        self.errors = [
            e for e in self.errors 
            if e.timestamp > cutoff
        ]

# Global error tracker instance
error_tracker = ErrorTracker()
