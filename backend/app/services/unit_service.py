from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import PropertyHubError
from app.db.models.property import Property
from app.db.models.unit import Unit
from app.schemas.unit import UnitCreate, UnitUpdate


class UnitService:
    def list_units(self, db: Session, organization_id: str) -> list[Unit]:
        statement = (
            select(Unit)
            .where(Unit.organization_id == organization_id)
            .order_by(Unit.created_at.desc())
        )
        return list(db.scalars(statement))

    def _ensure_property(self, db: Session, organization_id: str, property_id: str) -> Property:
        property_obj = db.scalar(
            select(Property).where(
                Property.id == property_id,
                Property.organization_id == organization_id,
            )
        )
        if property_obj is None:
            raise PropertyHubError("Property not found", status_code=404)
        return property_obj

    def get_unit(self, db: Session, organization_id: str, unit_id: str) -> Unit:
        unit = db.scalar(
            select(Unit).where(
                Unit.id == unit_id,
                Unit.organization_id == organization_id,
            )
        )
        if unit is None:
            raise PropertyHubError("Unit not found", status_code=404)
        return unit

    def create_unit(self, db: Session, organization_id: str, payload: UnitCreate) -> Unit:
        self._ensure_property(db, organization_id, payload.property_id)
        unit = Unit(organization_id=organization_id, **payload.model_dump())
        db.add(unit)
        db.commit()
        db.refresh(unit)
        return unit

    def update_unit(
        self, db: Session, organization_id: str, unit_id: str, payload: UnitUpdate
    ) -> Unit:
        self._ensure_property(db, organization_id, payload.property_id)
        unit = self.get_unit(db, organization_id, unit_id)
        for field, value in payload.model_dump().items():
            setattr(unit, field, value)
        db.add(unit)
        db.commit()
        db.refresh(unit)
        return unit

    def delete_unit(self, db: Session, organization_id: str, unit_id: str) -> None:
        unit = self.get_unit(db, organization_id, unit_id)
        db.delete(unit)
        db.commit()
