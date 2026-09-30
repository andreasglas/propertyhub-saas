from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import PropertyHubError
from app.db.models.contract import Contract
from app.db.models.operating_cost_item import OperatingCostItem
from app.db.models.operating_cost_period import OperatingCostPeriod
from app.db.models.property import Property
from app.db.models.tenant import Tenant
from app.db.models.unit import Unit
from app.schemas.operating_costs import (
    OperatingCostItemCreate,
    OperatingCostItemUpdate,
    OperatingCostPeriodCreate,
    OperatingCostPeriodRead,
    OperatingCostPeriodUpdate,
    OperatingCostSettlementLine,
    OperatingCostSettlementPreview,
)


class OperatingCostService:
    def list_periods(self, db: Session, organization_id: str) -> list[OperatingCostPeriod]:
        return list(
            db.scalars(
                select(OperatingCostPeriod)
                .where(OperatingCostPeriod.organization_id == organization_id)
                .order_by(
                    OperatingCostPeriod.period_end.desc(),
                    OperatingCostPeriod.created_at.desc(),
                )
            )
        )

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

    def get_period(
        self, db: Session, organization_id: str, period_id: str
    ) -> OperatingCostPeriod:
        period = db.scalar(
            select(OperatingCostPeriod).where(
                OperatingCostPeriod.id == period_id,
                OperatingCostPeriod.organization_id == organization_id,
            )
        )
        if period is None:
            raise PropertyHubError("Operating cost period not found", status_code=404)
        return period

    def create_period(
        self, db: Session, organization_id: str, payload: OperatingCostPeriodCreate
    ) -> OperatingCostPeriod:
        self._ensure_property(db, organization_id, payload.property_id)
        period = OperatingCostPeriod(organization_id=organization_id, **payload.model_dump())
        db.add(period)
        db.commit()
        db.refresh(period)
        return period

    def update_period(
        self,
        db: Session,
        organization_id: str,
        period_id: str,
        payload: OperatingCostPeriodUpdate,
    ) -> OperatingCostPeriod:
        self._ensure_property(db, organization_id, payload.property_id)
        period = self.get_period(db, organization_id, period_id)
        for key, value in payload.model_dump().items():
            setattr(period, key, value)
        db.add(period)
        db.commit()
        db.refresh(period)
        return period

    def delete_period(self, db: Session, organization_id: str, period_id: str) -> None:
        period = self.get_period(db, organization_id, period_id)
        items = db.scalars(
            select(OperatingCostItem).where(
                OperatingCostItem.organization_id == organization_id,
                OperatingCostItem.period_id == period_id,
            )
        )
        for item in items:
            db.delete(item)
        db.delete(period)
        db.commit()

    def list_items(
        self, db: Session, organization_id: str, period_id: str
    ) -> list[OperatingCostItem]:
        self.get_period(db, organization_id, period_id)
        return list(
            db.scalars(
                select(OperatingCostItem)
                .where(
                    OperatingCostItem.organization_id == organization_id,
                    OperatingCostItem.period_id == period_id,
                )
                .order_by(OperatingCostItem.created_at.desc())
            )
        )

    def get_item(self, db: Session, organization_id: str, item_id: str) -> OperatingCostItem:
        item = db.scalar(
            select(OperatingCostItem).where(
                OperatingCostItem.id == item_id,
                OperatingCostItem.organization_id == organization_id,
            )
        )
        if item is None:
            raise PropertyHubError("Operating cost item not found", status_code=404)
        return item

    def create_item(
        self,
        db: Session,
        organization_id: str,
        period_id: str,
        payload: OperatingCostItemCreate,
    ) -> OperatingCostItem:
        self.get_period(db, organization_id, period_id)
        item = OperatingCostItem(
            organization_id=organization_id,
            period_id=period_id,
            **payload.model_dump(),
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    def update_item(
        self,
        db: Session,
        organization_id: str,
        item_id: str,
        payload: OperatingCostItemUpdate,
    ) -> OperatingCostItem:
        item = self.get_item(db, organization_id, item_id)
        for key, value in payload.model_dump().items():
            setattr(item, key, value)
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    def delete_item(self, db: Session, organization_id: str, item_id: str) -> None:
        item = self.get_item(db, organization_id, item_id)
        db.delete(item)
        db.commit()

    def get_settlement_preview(
        self, db: Session, organization_id: str, period_id: str
    ) -> OperatingCostSettlementPreview:
        period = self.get_period(db, organization_id, period_id)
        items = self.list_items(db, organization_id, period_id)
        billable_items = [item for item in items if item.billable]
        total_billable_amount = sum(float(item.amount) for item in billable_items)

        units = list(
            db.scalars(
                select(Unit).where(
                    Unit.organization_id == organization_id,
                    Unit.property_id == period.property_id,
                )
            )
        )
        units_by_id = {unit.id: unit for unit in units}
        tenants_by_id = {
            tenant.id: tenant
            for tenant in db.scalars(
                select(Tenant).where(Tenant.organization_id == organization_id)
            )
        }
        contracts = [
            contract
            for contract in db.scalars(
                select(Contract).where(Contract.organization_id == organization_id)
            )
            if contract.unit_id in units_by_id and self._contract_overlaps_period(contract, period)
        ]

        if not contracts:
            return OperatingCostSettlementPreview(
                period=OperatingCostPeriodRead.model_validate(period),
                items=[item for item in items],
                total_billable_amount=round(total_billable_amount, 2),
                total_advance_amount=0,
                lines=[],
            )

        unit_count_total = max(len(contracts), 1)
        total_area = sum(float(units_by_id[contract.unit_id].area_sqm or 0) for contract in contracts)
        if total_area <= 0:
            total_area = float(unit_count_total)

        share_by_contract: dict[str, float] = {contract.id: 0.0 for contract in contracts}
        factor_by_contract: dict[str, float] = {contract.id: 0.0 for contract in contracts}

        for item in billable_items:
            for contract in contracts:
                unit = units_by_id[contract.unit_id]
                if item.allocation_method == "unit_count":
                    factor = 1 / unit_count_total
                else:
                    area = float(unit.area_sqm or 0)
                    factor = (area / total_area) if total_area > 0 else 0
                share = round(float(item.amount) * factor, 2)
                share_by_contract[contract.id] += share
                factor_by_contract[contract.id] += factor

        lines: list[OperatingCostSettlementLine] = []
        total_advance_amount = 0.0
        for contract in contracts:
            tenant = tenants_by_id.get(contract.tenant_id)
            months = self._overlap_months(contract.start_date, contract.end_date, period.period_start, period.period_end)
            advance_paid_amount = round(float(contract.service_charge_advance) * months, 2)
            total_advance_amount += advance_paid_amount
            share_amount = round(share_by_contract[contract.id], 2)
            lines.append(
                OperatingCostSettlementLine(
                    contract_id=contract.id,
                    tenant_id=contract.tenant_id,
                    tenant_name=(
                        f"{tenant.first_name} {tenant.last_name}".strip()
                        if tenant is not None
                        else contract.tenant_id
                    ),
                    unit_id=contract.unit_id,
                    unit_name=units_by_id[contract.unit_id].name,
                    allocation_factor=round(factor_by_contract[contract.id], 4),
                    share_amount=share_amount,
                    advance_paid_amount=advance_paid_amount,
                    balance_amount=round(share_amount - advance_paid_amount, 2),
                )
            )

        lines.sort(key=lambda line: (line.unit_name.lower(), line.tenant_name.lower()))
        return OperatingCostSettlementPreview(
            period=OperatingCostPeriodRead.model_validate(period),
            items=items,
            total_billable_amount=round(total_billable_amount, 2),
            total_advance_amount=round(total_advance_amount, 2),
            lines=lines,
        )

    def _contract_overlaps_period(
        self, contract: Contract, period: OperatingCostPeriod
    ) -> bool:
        if contract.start_date > period.period_end:
            return False
        if contract.end_date is not None and contract.end_date < period.period_start:
            return False
        return True

    def _overlap_months(
        self,
        contract_start: date,
        contract_end: date | None,
        period_start: date,
        period_end: date,
    ) -> int:
        effective_start = max(contract_start, period_start)
        effective_end = min(contract_end or period_end, period_end)
        if effective_end < effective_start:
            return 0
        return (
            (effective_end.year - effective_start.year) * 12
            + (effective_end.month - effective_start.month)
            + 1
        )
