from fastapi import APIRouter

from app.api.v1.endpoints import (
    accounting,
    audit_logs,
    auth,
    banking,
    contracts,
    documents,
    invoices,
    operating_costs,
    organization,
    payments,
    properties,
    reports,
    tenants,
    units,
    users,
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(audit_logs.router, prefix="/audit-logs", tags=["audit-logs"])
api_router.include_router(organization.router, prefix="/organization", tags=["organization"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(properties.router, prefix="/properties", tags=["properties"])
api_router.include_router(tenants.router, prefix="/tenants", tags=["tenants"])
api_router.include_router(units.router, prefix="/units", tags=["units"])
api_router.include_router(contracts.router, prefix="/contracts", tags=["contracts"])
api_router.include_router(invoices.router, prefix="/invoices", tags=["invoices"])
api_router.include_router(
    operating_costs.router, prefix="/operating-costs", tags=["operating-costs"]
)
api_router.include_router(payments.router, prefix="/payments", tags=["payments"])
api_router.include_router(banking.router, prefix="/banking", tags=["banking"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(accounting.router, prefix="/accounting", tags=["accounting"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])


@api_router.get("", tags=["system"])
async def api_info() -> dict[str, str]:
    return {"name": "PropertyHub API", "version": "v1"}
