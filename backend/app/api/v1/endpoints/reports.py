from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def reports_status() -> dict[str, str]:
    return {"module": "reports", "status": "ready"}
