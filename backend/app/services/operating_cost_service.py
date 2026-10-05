from __future__ import annotations

import csv
import io
from calendar import monthrange
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal, ROUND_DOWN

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
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
    OperatingCostItemRead,
    OperatingCostItemUpdate,
    OperatingCostPeriodCreate,
    OperatingCostPeriodRead,
    OperatingCostPeriodUpdate,
    OperatingCostSettlementLine,
    OperatingCostSettlementPreview,
)


@dataclass
class SettlementSegment:
    line_key: str
    line_type: str
    contract: Contract | None
    tenant: Tenant | None
    unit: Unit
    start_date: date
    end_date: date
    occupied_days: int
    area_sqm: Decimal
    advance_paid_amount: Decimal


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

    def finalize_period(
        self, db: Session, organization_id: str, period_id: str
    ) -> OperatingCostPeriod:
        period = self.get_period(db, organization_id, period_id)
        period.status = "finalized"
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
        property_obj = self._ensure_property(db, organization_id, period.property_id)
        items = self.list_items(db, organization_id, period_id)
        return self._build_settlement_preview(db, organization_id, property_obj, period, items)

    def export_settlement_csv(
        self,
        db: Session,
        organization_id: str,
        period_id: str,
    ) -> str:
        preview = self.get_settlement_preview(db, organization_id, period_id)
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["period", preview.period.name])
        writer.writerow(["property_id", preview.period.property_id])
        writer.writerow(["period_start", preview.period.period_start.isoformat()])
        writer.writerow(["period_end", preview.period.period_end.isoformat()])
        writer.writerow(["status", preview.period.status])
        writer.writerow([])
        writer.writerow(["items"])
        writer.writerow(["category", "description", "allocation_method", "amount", "billable"])
        for item in preview.items:
            writer.writerow(
                [
                    item.category,
                    item.description or "",
                    item.allocation_method,
                    item.amount,
                    item.billable,
                ]
            )
        writer.writerow([])
        writer.writerow(["settlement_lines"])
        writer.writerow(
            [
                "line_type",
                "tenant_name",
                "unit_name",
                "occupied_days",
                "allocation_factor",
                "share_amount",
                "advance_paid_amount",
                "balance_amount",
            ]
        )
        for line in preview.lines:
            writer.writerow(
                [
                    line.line_type,
                    line.tenant_name or "",
                    line.unit_name,
                    line.occupied_days,
                    line.allocation_factor,
                    line.share_amount,
                    line.advance_paid_amount,
                    line.balance_amount,
                ]
            )
        return output.getvalue()

    def export_settlement_pdf(
        self,
        db: Session,
        organization_id: str,
        period_id: str,
    ) -> bytes:
        preview = self.get_settlement_preview(db, organization_id, period_id)
        property_obj = self._ensure_property(db, organization_id, preview.period.property_id)
        buffer = io.BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        y = height - 50

        def write_line(text: str, *, indent: int = 0, gap: int = 16, bold: bool = False) -> None:
            nonlocal y
            if y < 50:
                pdf.showPage()
                y = height - 50
            pdf.setFont("Helvetica-Bold" if bold else "Helvetica", 10)
            pdf.drawString(40 + indent, y, text[:120])
            y -= gap

        write_line("PropertyHub Betriebskostenabrechnung", bold=True, gap=20)
        write_line(f"Periode: {preview.period.name}")
        write_line(f"Immobilie: {property_obj.name}")
        write_line(
            f"Zeitraum: {preview.period.period_start.isoformat()} bis {preview.period.period_end.isoformat()}"
        )
        write_line(f"Status: {preview.period.status}")
        write_line(
            f"Umlagefähige Summe: {self._format_currency(preview.total_billable_amount)} · Vorauszahlungen: {self._format_currency(preview.total_advance_amount)}"
        )
        y -= 4
        write_line("Kostenpositionen", bold=True)
        for item in preview.items:
            write_line(
                f"- {item.category}: {self._format_currency(item.amount)} · {item.allocation_method} · {'umlagefähig' if item.billable else 'nicht umlagefähig'}",
                indent=8,
            )
            if item.description:
                write_line(item.description, indent=20, gap=14)
        y -= 4
        write_line("Abrechnung", bold=True)
        for line in preview.lines:
            subject = line.tenant_name or "Leerstand"
            write_line(
                f"- {subject} · {line.unit_name} · {line.occupied_days} Tage",
                indent=8,
            )
            write_line(
                f"Anteil {self._format_currency(line.share_amount)} · Vorauszahlung {self._format_currency(line.advance_paid_amount)} · Saldo {self._format_currency(line.balance_amount)}",
                indent=20,
                gap=14,
            )
        if not preview.lines:
            write_line("Keine abrechenbaren Zeilen vorhanden.", indent=8)

        pdf.save()
        return buffer.getvalue()

    def _build_settlement_preview(
        self,
        db: Session,
        organization_id: str,
        property_obj: Property,
        period: OperatingCostPeriod,
        items: list[OperatingCostItem],
    ) -> OperatingCostSettlementPreview:
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
        segments = self._build_segments(period, units, contracts, tenants_by_id)
        billable_items = [item for item in items if item.billable]
        total_billable_amount = sum(float(item.amount) for item in billable_items)
        total_advance_amount = round(
            sum(float(segment.advance_paid_amount) for segment in segments if segment.contract is not None),
            2,
        )

        if not segments:
            return OperatingCostSettlementPreview(
                period=OperatingCostPeriodRead.model_validate(period),
                items=[OperatingCostItemRead.model_validate(item) for item in items],
                total_billable_amount=round(total_billable_amount, 2),
                total_advance_amount=0,
                lines=[],
            )

        share_by_line_key = {segment.line_key: Decimal("0.00") for segment in segments}
        line_segments: dict[str, SettlementSegment] = {}
        occupied_days_by_line_key: dict[str, int] = {}
        advance_by_line_key: dict[str, Decimal] = {}
        for segment in segments:
            if segment.line_key not in line_segments:
                line_segments[segment.line_key] = segment
            occupied_days_by_line_key[segment.line_key] = (
                occupied_days_by_line_key.get(segment.line_key, 0) + segment.occupied_days
            )
            advance_by_line_key[segment.line_key] = advance_by_line_key.get(
                segment.line_key, Decimal("0.00")
            ) + segment.advance_paid_amount

        for item in billable_items:
            allocations = self._allocate_item_amount(item, units, segments, period)
            for line_key, share in allocations.items():
                share_by_line_key[line_key] += share

        lines: list[OperatingCostSettlementLine] = []
        for line_key, segment in line_segments.items():
            share_amount = share_by_line_key[line_key]
            advance_paid_amount = advance_by_line_key.get(line_key, Decimal("0.00"))
            line_total = self._to_float(share_amount)
            total_ratio = (
                line_total / total_billable_amount if total_billable_amount > 0 else 0.0
            )
            lines.append(
                OperatingCostSettlementLine(
                    line_type=segment.line_type,
                    contract_id=segment.contract.id if segment.contract is not None else None,
                    tenant_id=segment.contract.tenant_id if segment.contract is not None else None,
                    tenant_name=(
                        f"{segment.tenant.first_name} {segment.tenant.last_name}".strip()
                        if segment.tenant is not None
                        else "Leerstand"
                    ),
                    unit_id=segment.unit.id,
                    unit_name=segment.unit.name,
                    allocation_factor=round(total_ratio, 4),
                    occupied_days=occupied_days_by_line_key.get(line_key, segment.occupied_days),
                    share_amount=line_total,
                    advance_paid_amount=self._to_float(advance_paid_amount),
                    balance_amount=self._to_float(share_amount - advance_paid_amount),
                )
            )

        lines.sort(key=lambda line: (line.unit_name.lower(), line.line_type, (line.tenant_name or "").lower()))
        return OperatingCostSettlementPreview(
            period=OperatingCostPeriodRead.model_validate(period),
            items=[OperatingCostItemRead.model_validate(item) for item in items],
            total_billable_amount=round(total_billable_amount, 2),
            total_advance_amount=round(total_advance_amount, 2),
            lines=lines,
        )

    def _allocate_item_amount(
        self,
        item: OperatingCostItem,
        units: list[Unit],
        segments: list[SettlementSegment],
        period: OperatingCostPeriod,
    ) -> dict[str, Decimal]:
        if not segments:
            return {}

        period_days = Decimal(str(self._days_between(period.period_start, period.period_end)))
        total_units = Decimal(str(max(len(units), 1)))
        total_area = sum((self._decimal(unit.area_sqm) for unit in units), Decimal("0"))
        occupied_segments = [segment for segment in segments if segment.contract is not None]
        occupied_days_total = sum(
            (Decimal(str(segment.occupied_days)) for segment in occupied_segments), Decimal("0")
        )
        advance_total = sum(
            (segment.advance_paid_amount for segment in occupied_segments if segment.advance_paid_amount > 0),
            Decimal("0"),
        )

        weights: list[tuple[str, Decimal]] = []
        if item.allocation_method == "unit_count":
            denominator = total_units * period_days
            weights = [
                (segment.line_key, Decimal(str(segment.occupied_days))) for segment in segments
            ]
        elif item.allocation_method == "occupancy_days":
            denominator = occupied_days_total
            weights = [
                (segment.line_key, Decimal(str(segment.occupied_days)))
                for segment in occupied_segments
            ]
        elif item.allocation_method == "advance_share":
            denominator = advance_total
            if denominator > 0:
                weights = [
                    (segment.line_key, segment.advance_paid_amount)
                    for segment in occupied_segments
                    if segment.advance_paid_amount > 0
                ]
            else:
                denominator = occupied_days_total
                weights = [
                    (segment.line_key, Decimal(str(segment.occupied_days)))
                    for segment in occupied_segments
                ]
        else:
            if total_area > 0:
                denominator = total_area * period_days
                weights = [
                    (
                        segment.line_key,
                        segment.area_sqm * Decimal(str(segment.occupied_days)),
                    )
                    for segment in segments
                ]
            else:
                denominator = total_units * period_days
                weights = [
                    (segment.line_key, Decimal(str(segment.occupied_days)))
                    for segment in segments
                ]

        filtered_weights = [(line_key, weight) for line_key, weight in weights if weight > 0]
        if not filtered_weights or denominator <= 0:
            return {}
        return self._distribute_amount(Decimal(str(item.amount)), filtered_weights, denominator)

    def _build_segments(
        self,
        period: OperatingCostPeriod,
        units: list[Unit],
        contracts: list[Contract],
        tenants_by_id: dict[str, Tenant],
    ) -> list[SettlementSegment]:
        segments: list[SettlementSegment] = []
        period_end_next = period.period_end + timedelta(days=1)

        for unit in units:
            unit_contracts = sorted(
                [contract for contract in contracts if contract.unit_id == unit.id],
                key=lambda contract: max(contract.start_date, period.period_start),
            )
            cursor = period.period_start
            for contract in unit_contracts:
                effective_start = max(contract.start_date, period.period_start, cursor)
                effective_end = min(contract.end_date or period.period_end, period.period_end)
                if effective_end < effective_start:
                    continue
                if effective_start > cursor:
                    segments.append(
                        self._create_vacancy_segment(unit, cursor, effective_start - timedelta(days=1))
                    )
                segments.append(
                    self._create_contract_segment(
                        unit,
                        contract,
                        tenants_by_id.get(contract.tenant_id),
                        effective_start,
                        effective_end,
                    )
                )
                cursor = effective_end + timedelta(days=1)
                if cursor >= period_end_next:
                    break
            if cursor <= period.period_end:
                segments.append(self._create_vacancy_segment(unit, cursor, period.period_end))
        return [segment for segment in segments if segment.occupied_days > 0]

    def _create_contract_segment(
        self,
        unit: Unit,
        contract: Contract,
        tenant: Tenant | None,
        start_date: date,
        end_date: date,
    ) -> SettlementSegment:
        occupied_days = self._days_between(start_date, end_date)
        return SettlementSegment(
            line_key=f"contract:{contract.id}",
            line_type="contract",
            contract=contract,
            tenant=tenant,
            unit=unit,
            start_date=start_date,
            end_date=end_date,
            occupied_days=occupied_days,
            area_sqm=self._decimal(unit.area_sqm),
            advance_paid_amount=self._prorated_advance_amount(
                self._decimal(contract.service_charge_advance),
                start_date,
                end_date,
            ),
        )

    def _create_vacancy_segment(
        self,
        unit: Unit,
        start_date: date,
        end_date: date,
    ) -> SettlementSegment:
        occupied_days = self._days_between(start_date, end_date)
        return SettlementSegment(
            line_key=f"vacancy:{unit.id}",
            line_type="vacancy",
            contract=None,
            tenant=None,
            unit=unit,
            start_date=start_date,
            end_date=end_date,
            occupied_days=occupied_days,
            area_sqm=self._decimal(unit.area_sqm),
            advance_paid_amount=Decimal("0.00"),
        )

    def _contract_overlaps_period(
        self, contract: Contract, period: OperatingCostPeriod
    ) -> bool:
        if contract.start_date > period.period_end:
            return False
        if contract.end_date is not None and contract.end_date < period.period_start:
            return False
        return True

    def _prorated_advance_amount(
        self,
        monthly_advance: Decimal,
        start_date: date,
        end_date: date,
    ) -> Decimal:
        total = Decimal("0")
        current = date(start_date.year, start_date.month, 1)
        last_month = date(end_date.year, end_date.month, 1)
        while current <= last_month:
            days_in_month = monthrange(current.year, current.month)[1]
            month_start = current
            month_end = date(current.year, current.month, days_in_month)
            overlap_start = max(start_date, month_start)
            overlap_end = min(end_date, month_end)
            if overlap_end >= overlap_start:
                overlap_days = Decimal(str(self._days_between(overlap_start, overlap_end)))
                total += monthly_advance * (overlap_days / Decimal(str(days_in_month)))
            if current.month == 12:
                current = date(current.year + 1, 1, 1)
            else:
                current = date(current.year, current.month + 1, 1)
        return total.quantize(Decimal("0.01"))

    def _distribute_amount(
        self,
        amount: Decimal,
        weights: list[tuple[str, Decimal]],
        denominator: Decimal,
    ) -> dict[str, Decimal]:
        total_cents = int((amount * 100).quantize(Decimal("1")))
        distributed_cents = 0
        allocations: list[tuple[str, int, Decimal]] = []
        for line_key, weight in weights:
            raw_cents = (Decimal(total_cents) * weight) / denominator
            cents = int(raw_cents.quantize(Decimal("1"), rounding=ROUND_DOWN))
            distributed_cents += cents
            allocations.append((line_key, cents, raw_cents - Decimal(cents)))

        remainder = total_cents - distributed_cents
        allocations.sort(key=lambda allocation: allocation[2], reverse=True)
        for index in range(remainder):
            line_key, cents, fractional = allocations[index % len(allocations)]
            allocations[index % len(allocations)] = (line_key, cents + 1, fractional)

        result: dict[str, Decimal] = {}
        for line_key, cents, _ in allocations:
            result[line_key] = result.get(line_key, Decimal("0.00")) + (Decimal(cents) / Decimal("100"))
        return result

    def _days_between(self, start_date: date, end_date: date) -> int:
        return (end_date - start_date).days + 1

    def _decimal(self, value: Decimal | float | int | None) -> Decimal:
        if value is None:
            return Decimal("0")
        if isinstance(value, Decimal):
            return value
        return Decimal(str(value))

    def _to_float(self, value: Decimal) -> float:
        return float(value.quantize(Decimal("0.01")))

    def _format_currency(self, value: float) -> str:
        return f"{value:.2f} €"
