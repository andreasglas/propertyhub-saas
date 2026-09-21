from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_contracts() -> dict[str, object]:
    return {"module": "contracts", "status": "ready", "items": []}
