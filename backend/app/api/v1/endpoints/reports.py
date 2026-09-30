from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.report import DashboardReportRead, OpenInvoiceReportRow
from app.services.report_service import ReportService

router = APIRouter()
service = ReportService()


@router.get("/", response_model=DashboardReportRead)
async def reports_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DashboardReportRead:
    return service.get_dashboard_summary(db, current_user.organization_id)


@router.get("/open-invoices", response_model=list[OpenInvoiceReportRow])
async def open_invoices_report(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[OpenInvoiceReportRow]:
    return service.list_open_invoices(db, current_user.organization_id)


@router.get("/export/dashboard.csv")
async def export_dashboard_csv(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    summary = service.get_dashboard_summary(db, current_user.organization_id)
    content = service.export_dashboard_summary_csv(summary)
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="dashboard-summary.csv"'},
    )


@router.get("/export/open-invoices.csv")
async def export_open_invoices_csv(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    rows = service.list_open_invoices(db, current_user.organization_id)
    content = service.export_open_invoices_csv(rows)
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="open-invoices.csv"'},
    )
