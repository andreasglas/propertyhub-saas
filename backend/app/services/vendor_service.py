from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import PropertyHubError
from app.db.models.vendor import Vendor
from app.schemas.vendor import VendorCreate, VendorUpdate


class VendorService:
    def list_vendors(self, db: Session, organization_id: str) -> list[Vendor]:
        return list(
            db.scalars(
                select(Vendor)
                .where(Vendor.organization_id == organization_id)
                .order_by(Vendor.name.asc(), Vendor.created_at.desc())
            )
        )

    def get_vendor(self, db: Session, organization_id: str, vendor_id: str) -> Vendor:
        vendor = db.scalar(
            select(Vendor).where(
                Vendor.id == vendor_id,
                Vendor.organization_id == organization_id,
            )
        )
        if vendor is None:
            raise PropertyHubError("Vendor not found", status_code=404)
        return vendor

    def create_vendor(self, db: Session, organization_id: str, payload: VendorCreate) -> Vendor:
        vendor = Vendor(organization_id=organization_id, **payload.model_dump())
        db.add(vendor)
        db.commit()
        db.refresh(vendor)
        return vendor

    def update_vendor(
        self, db: Session, organization_id: str, vendor_id: str, payload: VendorUpdate
    ) -> Vendor:
        vendor = self.get_vendor(db, organization_id, vendor_id)
        for key, value in payload.model_dump().items():
            setattr(vendor, key, value)
        db.add(vendor)
        db.commit()
        db.refresh(vendor)
        return vendor

    def delete_vendor(self, db: Session, organization_id: str, vendor_id: str) -> None:
        vendor = self.get_vendor(db, organization_id, vendor_id)
        db.delete(vendor)
        db.commit()
