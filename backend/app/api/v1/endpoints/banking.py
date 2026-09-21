from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def banking_status() -> dict[str, str]:
    return {"module": "banking", "status": "ready"}
