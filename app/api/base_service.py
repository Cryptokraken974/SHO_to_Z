"""
Base Service Class

Provides common functionality for all API service classes including:
- HTTP client management
- Error handling
- Response parsing
- Logging
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Union
from abc import ABC, abstractmethod
import aiohttp
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class ServiceError(Exception):
    """Custom exception for service layer errors"""
    def __init__(self, message: str, status_code: Optional[int] = None, details: Optional[Dict] = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class BaseService(ABC):
    """
    Abstract base class for all API services
    
    Provides common functionality like HTTP client management,
    error handling, and response processing.
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize the service
        
        Args:
            base_url: Base URL for the API server
        """
        self.base_url = base_url.rstrip('/')
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=300)  # 5 minutes
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session
    
    async def close(self):
        """Close the HTTP session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        form_data: Optional[aiohttp.FormData] = None,
        headers: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request to API endpoint
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            params: URL parameters
            json_data: JSON payload
            form_data: Form data for file uploads
            headers: Additional headers
            
        Returns:
            Response data as dictionary
            
        Raises:
            ServiceError: If request fails or returns error status
        """
        session = await self._get_session()
        url = f"{self.base_url}{endpoint}"
        
        try:
            logger.debug(f"Making {method} request to {url}")
            
            kwargs = {}
            if params:
                kwargs['params'] = params
            if json_data:
                kwargs['json'] = json_data
            if form_data:
                kwargs['data'] = form_data
            if headers:
                kwargs['headers'] = headers
                
            async with session.request(method, url, **kwargs) as response:
                # Try to parse response as JSON
                try:
                    response_data = await response.json()
                except (json.JSONDecodeError, aiohttp.ContentTypeError):
                    # Fallback to text response
                    response_text = await response.text()
                    response_data = {"message": response_text}
                
                # Check for HTTP errors
                if response.status >= 400:
                    error_message = response_data.get('detail', f"HTTP {response.status} error")
                    raise ServiceError(
                        message=error_message,
                        status_code=response.status,
                        details=response_data
                    )
                
                logger.debug(f"Request successful: {response.status}")
                return response_data
                
        except aiohttp.ClientError as e:
            logger.error(f"Client error in {method} {url}: {e}")
            raise ServiceError(f"Network error: {str(e)}")
        except asyncio.TimeoutError:
            logger.error(f"Timeout in {method} {url}")
            raise ServiceError("Request timeout")
        except Exception as e:
            logger.error(f"Unexpected error in {method} {url}: {e}")
            raise ServiceError(f"Unexpected error: {str(e)}")
    
    async def _get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make GET request"""
        return await self._make_request('GET', endpoint, params=params)
    
    async def _post(
        self,
        endpoint: str,
        json_data: Optional[Dict] = None,
        form_data: Optional[aiohttp.FormData] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make POST request"""
        return await self._make_request('POST', endpoint, params=params, json_data=json_data, form_data=form_data)
    
    async def _put(
        self,
        endpoint: str,
        json_data: Optional[Dict] = None,
        form_data: Optional[aiohttp.FormData] = None
    ) -> Dict[str, Any]:
        """Make PUT request"""
        return await self._make_request('PUT', endpoint, json_data=json_data, form_data=form_data)
    
    async def _delete(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make DELETE request"""
        return await self._make_request('DELETE', endpoint, params=params)
    
    def _prepare_form_data(self, data: Dict[str, Any]) -> aiohttp.FormData:
        """
        Prepare form data for multipart requests
        
        Args:
            data: Dictionary containing form fields and files
            
        Returns:
            Prepared FormData object
        """
        form_data = aiohttp.FormData()
        
        for key, value in data.items():
            if isinstance(value, (str, int, float, bool)):
                form_data.add_field(key, str(value))
            elif isinstance(value, (bytes, bytearray)):
                form_data.add_field(key, value)
            elif hasattr(value, 'read'):  # File-like object
                filename = getattr(value, 'name', key)
                form_data.add_field(key, value, filename=filename)
            else:
                # Convert complex objects to JSON string
                form_data.add_field(key, json.dumps(value))
        
        return form_data
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()


class SyncServiceMixin:
    """
    Mixin to provide synchronous versions of async methods
    
    This allows services to be used in both async and sync contexts.
    """
    
    def _run_async(self, coro):
        """Run async coroutine in sync context"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're already in an async context, we can't use run_until_complete
                # This should be called from async context instead
                raise RuntimeError("Cannot call sync method from async context. Use async version instead.")
            else:
                return loop.run_until_complete(coro)
        except RuntimeError:
            # No event loop, create a new one
            return asyncio.run(coro)
