from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_units() -> dict[str, object]:
    return {"module": "units", "status": "ready", "items": []}
