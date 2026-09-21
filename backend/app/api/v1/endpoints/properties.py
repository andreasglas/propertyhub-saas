from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_properties() -> dict[str, object]:
    return {"module": "properties", "status": "ready", "items": []}
