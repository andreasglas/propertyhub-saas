from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_invoices() -> dict[str, object]:
    return {"module": "invoices", "status": "ready", "items": []}
