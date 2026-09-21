from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import PropertyHubError
from app.db.models.property import Property
from app.schemas.property import PropertyCreate, PropertyUpdate


class PropertyService:
    def list_properties(self, db: Session, organization_id: str) -> list[Property]:
        statement = (
            select(Property)
            .where(Property.organization_id == organization_id)
            .order_by(Property.created_at.desc())
        )
        return list(db.scalars(statement))

    def get_property(self, db: Session, organization_id: str, property_id: str) -> Property:
        property_obj = db.scalar(
            select(Property).where(
                Property.id == property_id,
                Property.organization_id == organization_id,
            )
        )
        if property_obj is None:
            raise PropertyHubError("Property not found", status_code=404)
        return property_obj

    def create_property(
        self, db: Session, organization_id: str, payload: PropertyCreate
    ) -> Property:
        property_obj = Property(organization_id=organization_id, **payload.model_dump())
        db.add(property_obj)
        db.commit()
        db.refresh(property_obj)
        return property_obj

    def update_property(
        self,
        db: Session,
        organization_id: str,
        property_id: str,
        payload: PropertyUpdate,
    ) -> Property:
        property_obj = self.get_property(db, organization_id, property_id)
        for field, value in payload.model_dump().items():
            setattr(property_obj, field, value)
        db.add(property_obj)
        db.commit()
        db.refresh(property_obj)
        return property_obj

    def delete_property(self, db: Session, organization_id: str, property_id: str) -> None:
        property_obj = self.get_property(db, organization_id, property_id)
        db.delete(property_obj)
        db.commit()
