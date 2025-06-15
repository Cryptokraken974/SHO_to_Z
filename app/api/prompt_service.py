from typing import Dict, Any
from .base_service import BaseService, SyncServiceMixin


class PromptService(BaseService, SyncServiceMixin):
    """Service for retrieving LLM prompts."""

    async def get_all_prompts(self) -> Dict[str, Any]:
        return await self._get("/api/prompts/all")
