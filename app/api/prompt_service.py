from typing import Dict, Any
from .base_service import BaseService, SyncServiceMixin


class PromptService(BaseService, SyncServiceMixin):
    """Service for retrieving LLM prompts."""

    async def get_all_prompts(self) -> Dict[str, Any]:
        return await self._get("/api/prompts/all")
    
    async def get_workflow_prompts(self, workflow: str = "workflow") -> Dict[str, Any]:
        """Get prompts from a specific workflow folder."""
        return await self._get(f"/api/prompts/workflow?workflow={workflow}")
