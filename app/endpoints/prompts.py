from fastapi import APIRouter
from pathlib import Path

router = APIRouter()

@router.get("/api/prompts/all")
async def get_all_prompts() -> dict:
    """Concatenate all prompt files and return as a single string."""
    base_dir = Path("llm/prompts")
    parts = []
    for file_path in sorted(base_dir.rglob("*.json")):
        try:
            parts.append(file_path.read_text(encoding="utf-8"))
        except Exception:
            continue
    return {"content": "\n".join(parts)}
