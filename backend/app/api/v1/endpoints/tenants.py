from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_tenants() -> dict[str, object]:
    return {"module": "tenants", "status": "ready", "items": []}
