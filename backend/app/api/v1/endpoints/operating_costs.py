from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_roles
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.operating_costs import (
    OperatingCostItemCreate,
    OperatingCostItemRead,
    OperatingCostItemUpdate,
    OperatingCostPeriodCreate,
    OperatingCostPeriodRead,
    OperatingCostPeriodUpdate,
    OperatingCostSettlementPreview,
)
from app.services.audit_log_service import AuditLogService
from app.services.operating_cost_service import OperatingCostService

router = APIRouter()
service = OperatingCostService()
audit_service = AuditLogService()


@router.get("/periods", response_model=list[OperatingCostPeriodRead])
async def list_operating_cost_periods(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[OperatingCostPeriodRead]:
    return service.list_periods(db, current_user.organization_id)


@router.post("/periods", response_model=OperatingCostPeriodRead, status_code=status.HTTP_201_CREATED)
async def create_operating_cost_period(
    payload: OperatingCostPeriodCreate,
    current_user: User = Depends(require_roles("owner", "manager")),
    db: Session = Depends(get_db),
) -> OperatingCostPeriodRead:
    period = service.create_period(db, current_user.organization_id, payload)
    audit_service.record(
        db,
        organization_id=current_user.organization_id,
        actor=current_user,
        action="operating_cost_period.created",
        resource_type="operating_cost_period",
        resource_id=period.id,
        summary=f"Nebenkostenperiode {period.name} angelegt",
        details={"property_id": period.property_id, "status": period.status},
    )
    return period


@router.put("/periods/{period_id}", response_model=OperatingCostPeriodRead)
async def update_operating_cost_period(
    period_id: str,
    payload: OperatingCostPeriodUpdate,
    current_user: User = Depends(require_roles("owner", "manager")),
    db: Session = Depends(get_db),
) -> OperatingCostPeriodRead:
    period = service.update_period(db, current_user.organization_id, period_id, payload)
    audit_service.record(
        db,
        organization_id=current_user.organization_id,
        actor=current_user,
        action="operating_cost_period.updated",
        resource_type="operating_cost_period",
        resource_id=period.id,
        summary=f"Nebenkostenperiode {period.name} aktualisiert",
        details={"property_id": period.property_id, "status": period.status},
    )
    return period


@router.delete("/periods/{period_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_operating_cost_period(
    period_id: str,
    current_user: User = Depends(require_roles("owner", "manager")),
    db: Session = Depends(get_db),
) -> Response:
    period = service.get_period(db, current_user.organization_id, period_id)
    service.delete_period(db, current_user.organization_id, period_id)
    audit_service.record(
        db,
        organization_id=current_user.organization_id,
        actor=current_user,
        action="operating_cost_period.deleted",
        resource_type="operating_cost_period",
        resource_id=period_id,
        summary=f"Nebenkostenperiode {period.name} gelöscht",
        details={"property_id": period.property_id},
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/periods/{period_id}/finalize", response_model=OperatingCostPeriodRead)
async def finalize_operating_cost_period(
    period_id: str,
    current_user: User = Depends(require_roles("owner", "manager")),
    db: Session = Depends(get_db),
) -> OperatingCostPeriodRead:
    period = service.finalize_period(db, current_user.organization_id, period_id)
    audit_service.record(
        db,
        organization_id=current_user.organization_id,
        actor=current_user,
        action="operating_cost_period.finalized",
        resource_type="operating_cost_period",
        resource_id=period.id,
        summary=f"Nebenkostenperiode {period.name} finalisiert",
        details={"property_id": period.property_id, "status": period.status},
    )
    return period


@router.get("/periods/{period_id}/items", response_model=list[OperatingCostItemRead])
async def list_operating_cost_items(
    period_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[OperatingCostItemRead]:
    return service.list_items(db, current_user.organization_id, period_id)


@router.post(
    "/periods/{period_id}/items",
    response_model=OperatingCostItemRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_operating_cost_item(
    period_id: str,
    payload: OperatingCostItemCreate,
    current_user: User = Depends(require_roles("owner", "manager")),
    db: Session = Depends(get_db),
) -> OperatingCostItemRead:
    item = service.create_item(db, current_user.organization_id, period_id, payload)
    audit_service.record(
        db,
        organization_id=current_user.organization_id,
        actor=current_user,
        action="operating_cost_item.created",
        resource_type="operating_cost_item",
        resource_id=item.id,
        summary=f"Nebenkostenposition {item.category} angelegt",
        details={"period_id": item.period_id, "allocation_method": item.allocation_method, "amount": item.amount},
    )
    return item


@router.put("/items/{item_id}", response_model=OperatingCostItemRead)
async def update_operating_cost_item(
    item_id: str,
    payload: OperatingCostItemUpdate,
    current_user: User = Depends(require_roles("owner", "manager")),
    db: Session = Depends(get_db),
) -> OperatingCostItemRead:
    item = service.update_item(db, current_user.organization_id, item_id, payload)
    audit_service.record(
        db,
        organization_id=current_user.organization_id,
        actor=current_user,
        action="operating_cost_item.updated",
        resource_type="operating_cost_item",
        resource_id=item.id,
        summary=f"Nebenkostenposition {item.category} aktualisiert",
        details={"period_id": item.period_id, "allocation_method": item.allocation_method, "amount": item.amount},
    )
    return item


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_operating_cost_item(
    item_id: str,
    current_user: User = Depends(require_roles("owner", "manager")),
    db: Session = Depends(get_db),
) -> Response:
    item = service.get_item(db, current_user.organization_id, item_id)
    service.delete_item(db, current_user.organization_id, item_id)
    audit_service.record(
        db,
        organization_id=current_user.organization_id,
        actor=current_user,
        action="operating_cost_item.deleted",
        resource_type="operating_cost_item",
        resource_id=item_id,
        summary=f"Nebenkostenposition {item.category} gelöscht",
        details={"period_id": item.period_id, "allocation_method": item.allocation_method},
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/periods/{period_id}/settlement-preview", response_model=OperatingCostSettlementPreview)
async def get_operating_cost_settlement_preview(
    period_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OperatingCostSettlementPreview:
    return service.get_settlement_preview(db, current_user.organization_id, period_id)


@router.get("/periods/{period_id}/export.csv")
async def export_operating_cost_settlement_csv(
    period_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    period = service.get_period(db, current_user.organization_id, period_id)
    content = service.export_settlement_csv(db, current_user.organization_id, period_id)
    audit_service.record(
        db,
        organization_id=current_user.organization_id,
        actor=current_user,
        action="operating_cost_period.exported_csv",
        resource_type="operating_cost_period",
        resource_id=period.id,
        summary=f"Nebenkostenabrechnung {period.name} als CSV exportiert",
        details={"property_id": period.property_id, "status": period.status},
    )
    return Response(
        content=content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename=\"operating-cost-settlement-{period.id}.csv\"'
        },
    )


@router.get("/periods/{period_id}/export.pdf")
async def export_operating_cost_settlement_pdf(
    period_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    period = service.get_period(db, current_user.organization_id, period_id)
    content = service.export_settlement_pdf(db, current_user.organization_id, period_id)
    audit_service.record(
        db,
        organization_id=current_user.organization_id,
        actor=current_user,
        action="operating_cost_period.exported_pdf",
        resource_type="operating_cost_period",
        resource_id=period.id,
        summary=f"Nebenkostenabrechnung {period.name} als PDF exportiert",
        details={"property_id": period.property_id, "status": period.status},
    )
    return Response(
        content=content,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename=\"operating-cost-settlement-{period.id}.pdf\"'
        },
    )
