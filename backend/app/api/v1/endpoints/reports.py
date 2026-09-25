from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.report import DashboardReportRead
from app.services.report_service import ReportService

router = APIRouter()
service = ReportService()


@router.get("/", response_model=DashboardReportRead)
async def reports_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DashboardReportRead:
    return service.get_dashboard_summary(db, current_user.organization_id)
