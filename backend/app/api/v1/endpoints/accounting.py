from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def accounting_status() -> dict[str, str]:
    return {"module": "accounting", "status": "ready"}
