import { ChangeEvent, FormEvent, ReactNode, useEffect, useMemo, useState } from "react";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Grid,
  List,
  ListItem,
  ListItemText,
  MenuItem,
  Pagination,
  Stack,
  TextField,
  Typography,
} from "@mui/material";

import { AppRoute } from "../appRoutes";
import { useAuth } from "../context/AuthContext";
import {
  AccountingEntry,
  createAccountingEntry,
  listAccountingEntries,
} from "../services/accountingService";
import {
  BankTransaction,
  importBankTransactions,
  listBankTransactions,
  matchBankTransaction,
} from "../services/bankingService";
import {
  Contract,
  createContract,
  listContracts,
} from "../services/contractService";
import {
  applyDocumentOcrToInvoice,
  DocumentRecord,
  listDocuments,
  processDocumentOcr,
  uploadDocument,
} from "../services/documentService";
import { createInvoice, Invoice, listInvoices } from "../services/invoiceService";
import { createPayment, listPayments, Payment } from "../services/paymentService";
import {
  createProperty,
  Property,
  listProperties,
} from "../services/propertyService";
import { DashboardReport, getDashboardReport } from "../services/reportService";
import {
  Tenant,
  createTenant,
  listTenants,
} from "../services/tenantService";
import {
  Unit,
  createUnit,
  listUnits,
} from "../services/unitService";

const defaultCredentials = {
  email: "admin@example.com",
  password: "test-password",
};

const defaultListControls = {
  search: "",
  page: 1,
  pageSize: 5,
};

type DashboardPageProps = {
  currentRoute: AppRoute;
};

type ListControls = {
  search: string;
  page: number;
  pageSize: number;
};

type InvoiceListControls = ListControls & {
  status: string;
};

type UnitListControls = ListControls & {
  property_id: string;
  status: string;
};

type ContractListControls = ListControls & {
  unit_id: string;
  tenant_id: string;
};

type DocumentListControls = ListControls & {
  ocr_status: string;
  related_model: string;
};

type BankTransactionListControls = ListControls & {
  status: string;
};

type SelectOption = {
  value: string;
  label: string;
};

type ManagedListCardProps<T> = {
  title: string;
  items: T[];
  emptyText: string;
  searchValue: string;
  onSearchChange: (value: string) => void;
  page: number;
  onPageChange: (page: number) => void;
  pageSize: number;
  onPageSizeChange: (pageSize: number) => void;
  searchLabel?: string;
  extraFilters?: ReactNode;
  helperText?: string;
  renderPrimary: (item: T) => ReactNode;
  renderSecondary?: (item: T) => ReactNode;
  renderDetails?: (item: T) => ReactNode;
  renderActions?: (item: T) => ReactNode;
};

function matchesSearch(
  searchValue: string,
  values: Array<string | number | null | undefined>,
) {
  const normalizedSearch = searchValue.trim().toLowerCase();
  if (!normalizedSearch) {
    return true;
  }

  return values.some((value) =>
    String(value ?? "")
      .toLowerCase()
      .includes(normalizedSearch),
  );
}

function formatCurrency(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return "-";
  }
  return `${value.toFixed(2)} €`;
}

function formatTenantName(tenant: Tenant) {
  return `${tenant.first_name} ${tenant.last_name}`.trim();
}

function formatPropertyLocation(property: Property) {
  const parts = [
    property.street ?? null,
    property.postal_code || property.city
      ? `${property.postal_code ?? ""} ${property.city ?? ""}`.trim()
      : null,
  ].filter(Boolean);

  return parts.length ? parts.join(" · ") : "Keine Adressdaten";
}

function ManagedListCard<T>({
  title,
  items,
  emptyText,
  searchValue,
  onSearchChange,
  page,
  onPageChange,
  pageSize,
  onPageSizeChange,
  searchLabel = "Suche",
  extraFilters,
  helperText,
  renderPrimary,
  renderSecondary,
  renderDetails,
  renderActions,
}: ManagedListCardProps<T>) {
  const pageCount = Math.max(1, Math.ceil(items.length / pageSize));
  const currentPage = Math.min(page, pageCount);
  const visibleItems = items.slice((currentPage - 1) * pageSize, currentPage * pageSize);

  return (
    <Card>
      <CardContent>
        <Stack spacing={2}>
          <Stack
            direction={{ xs: "column", lg: "row" }}
            spacing={2}
            alignItems={{ xs: "stretch", lg: "center" }}
            justifyContent="space-between"
          >
            <div>
              <Typography variant="h6">{title}</Typography>
              <Typography color="text.secondary" variant="body2">
                {items.length} Einträge nach Filter
              </Typography>
            </div>
            <Stack
              direction={{ xs: "column", md: "row" }}
              spacing={2}
              alignItems={{ xs: "stretch", md: "center" }}
            >
              {extraFilters}
              <TextField
                size="small"
                label={searchLabel}
                value={searchValue}
                onChange={(event) => onSearchChange(event.target.value)}
              />
              <TextField
                select
                size="small"
                label="Pro Seite"
                value={String(pageSize)}
                onChange={(event) => onPageSizeChange(Number(event.target.value))}
                sx={{ minWidth: 120 }}
              >
                {[5, 10, 25].map((option) => (
                  <MenuItem key={option} value={String(option)}>
                    {option}
                  </MenuItem>
                ))}
              </TextField>
            </Stack>
          </Stack>

          {helperText ? (
            <Typography color="text.secondary" variant="body2">
              {helperText}
            </Typography>
          ) : null}

          <List dense>
            {visibleItems.map((item, index) => (
              <ListItem
                key={index}
                disableGutters
                sx={{ alignItems: "flex-start", flexDirection: "column", gap: 1.5 }}
              >
                <ListItemText
                  primary={renderPrimary(item)}
                  secondary={renderSecondary ? renderSecondary(item) : undefined}
                />
                {renderDetails ? renderDetails(item) : null}
                {renderActions ? renderActions(item) : null}
              </ListItem>
            ))}
            {!visibleItems.length ? (
              <Typography color="text.secondary">{emptyText}</Typography>
            ) : null}
          </List>

          {pageCount > 1 ? (
            <Box display="flex" justifyContent="flex-end">
              <Pagination
                count={pageCount}
                page={currentPage}
                onChange={(_, nextPage) => onPageChange(nextPage)}
                color="primary"
              />
            </Box>
          ) : null}
        </Stack>
      </CardContent>
    </Card>
  );
}

export function DashboardPage({ currentRoute }: DashboardPageProps) {
  const { canManageData, currentUser, isAuthenticated, isLoadingUser, login } = useAuth();

  const [email, setEmail] = useState(defaultCredentials.email);
  const [password, setPassword] = useState(defaultCredentials.password);
  const [loginError, setLoginError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);

  const [properties, setProperties] = useState<Property[]>([]);
  const [units, setUnits] = useState<Unit[]>([]);
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [entries, setEntries] = useState<AccountingEntry[]>([]);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [payments, setPayments] = useState<Payment[]>([]);
  const [bankTransactions, setBankTransactions] = useState<BankTransaction[]>([]);
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [report, setReport] = useState<DashboardReport | null>(null);

  const [bankingActionLoading, setBankingActionLoading] = useState(false);
  const [documentActionLoading, setDocumentActionLoading] = useState(false);
  const [selectedDocumentFile, setSelectedDocumentFile] = useState<File | null>(null);

  const [propertyForm, setPropertyForm] = useState({
    name: "",
    property_type: "residential",
    street: "",
    city: "",
    postal_code: "",
    purchase_price: "",
  });
  const [unitForm, setUnitForm] = useState({
    property_id: "",
    name: "",
    unit_type: "apartment",
    status: "vacant",
    area_sqm: "",
  });
  const [tenantForm, setTenantForm] = useState({
    first_name: "",
    last_name: "",
    email: "",
    phone: "",
    move_in_date: "",
    move_out_date: "",
  });
  const [contractForm, setContractForm] = useState({
    unit_id: "",
    tenant_id: "",
    start_date: "",
    end_date: "",
    cold_rent: "0",
    service_charge_advance: "0",
  });
  const [entryForm, setEntryForm] = useState({
    property_id: "",
    entry_type: "expense",
    category: "insurance",
    amount: "0",
    booking_date: "",
  });
  const [invoiceForm, setInvoiceForm] = useState({
    property_id: "",
    vendor_name: "",
    invoice_number: "",
    invoice_date: "",
    gross_amount: "0",
    status: "received",
  });
  const [paymentForm, setPaymentForm] = useState({
    invoice_id: "",
    amount: "0",
    booking_date: "",
    reference: "",
  });
  const [documentForm, setDocumentForm] = useState({
    related_model: "invoice",
    related_id: "",
    document_type: "invoice_receipt",
  });

  const [propertyList, setPropertyList] = useState<ListControls>(defaultListControls);
  const [unitList, setUnitList] = useState<UnitListControls>({
    ...defaultListControls,
    property_id: "all",
    status: "all",
  });
  const [tenantList, setTenantList] = useState<ListControls>(defaultListControls);
  const [contractList, setContractList] = useState<ContractListControls>({
    ...defaultListControls,
    unit_id: "all",
    tenant_id: "all",
  });
  const [invoiceList, setInvoiceList] = useState<InvoiceListControls>({
    ...defaultListControls,
    status: "all",
  });
  const [paymentList, setPaymentList] = useState<ListControls>(defaultListControls);
  const [bankTransactionList, setBankTransactionList] = useState<BankTransactionListControls>({
    ...defaultListControls,
    status: "all",
  });
  const [documentList, setDocumentList] = useState<DocumentListControls>({
    ...defaultListControls,
    ocr_status: "all",
    related_model: "all",
  });

  async function loadDashboardData() {
    setLoading(true);
    setLoadError(null);
    try {
      const [
        loadedProperties,
        loadedUnits,
        loadedTenants,
        loadedContracts,
        loadedEntries,
        loadedInvoices,
        loadedPayments,
        loadedBankTransactions,
        loadedDocuments,
        loadedReport,
      ] = await Promise.all([
        listProperties(),
        listUnits(),
        listTenants(),
        listContracts(),
        listAccountingEntries(),
        listInvoices(),
        listPayments(),
        listBankTransactions(),
        listDocuments(),
        getDashboardReport(),
      ]);

      setProperties(loadedProperties);
      setUnits(loadedUnits);
      setTenants(loadedTenants);
      setContracts(loadedContracts);
      setEntries(loadedEntries);
      setInvoices(loadedInvoices);
      setPayments(loadedPayments);
      setBankTransactions(loadedBankTransactions);
      setDocuments(loadedDocuments);
      setReport(loadedReport);
    } catch {
      setLoadError("Daten konnten nicht geladen werden.");
    } finally {
      setLoading(false);
    }
  }

  async function handleLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoginError(null);
    try {
      await login(email, password);
    } catch {
      setLoginError("Login fehlgeschlagen. Bitte Zugangsdaten prüfen.");
    }
  }

  async function handleCreateProperty(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      await createProperty({
        name: propertyForm.name,
        property_type: propertyForm.property_type,
        street: propertyForm.street || null,
        city: propertyForm.city || null,
        postal_code: propertyForm.postal_code || null,
        purchase_price: propertyForm.purchase_price ? Number(propertyForm.purchase_price) : null,
      });
      setPropertyForm({
        name: "",
        property_type: "residential",
        street: "",
        city: "",
        postal_code: "",
        purchase_price: "",
      });
      await loadDashboardData();
    } catch {
      setLoadError("Immobilie konnte nicht gespeichert werden.");
    }
  }

  async function handleCreateUnit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      await createUnit({
        property_id: unitForm.property_id,
        name: unitForm.name,
        unit_type: unitForm.unit_type,
        status: unitForm.status,
        area_sqm: unitForm.area_sqm ? Number(unitForm.area_sqm) : null,
      });
      setUnitForm({
        property_id: "",
        name: "",
        unit_type: "apartment",
        status: "vacant",
        area_sqm: "",
      });
      await loadDashboardData();
    } catch {
      setLoadError("Einheit konnte nicht gespeichert werden.");
    }
  }

  async function handleCreateTenant(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      await createTenant({
        first_name: tenantForm.first_name,
        last_name: tenantForm.last_name,
        email: tenantForm.email || null,
        phone: tenantForm.phone || null,
        move_in_date: tenantForm.move_in_date || null,
        move_out_date: tenantForm.move_out_date || null,
      });
      setTenantForm({
        first_name: "",
        last_name: "",
        email: "",
        phone: "",
        move_in_date: "",
        move_out_date: "",
      });
      await loadDashboardData();
    } catch {
      setLoadError("Mieter konnte nicht gespeichert werden.");
    }
  }

  async function handleCreateContract(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      await createContract({
        unit_id: contractForm.unit_id,
        tenant_id: contractForm.tenant_id,
        start_date: contractForm.start_date,
        end_date: contractForm.end_date || null,
        cold_rent: Number(contractForm.cold_rent),
        service_charge_advance: Number(contractForm.service_charge_advance),
      });
      setContractForm({
        unit_id: "",
        tenant_id: "",
        start_date: "",
        end_date: "",
        cold_rent: "0",
        service_charge_advance: "0",
      });
      await loadDashboardData();
    } catch {
      setLoadError("Vertrag konnte nicht gespeichert werden.");
    }
  }

  async function handleCreateEntry(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      await createAccountingEntry({
        property_id: entryForm.property_id || null,
        entry_type: entryForm.entry_type,
        category: entryForm.category || null,
        amount: Number(entryForm.amount),
        booking_date: entryForm.booking_date || null,
      });
      setEntryForm({
        property_id: "",
        entry_type: "expense",
        category: "insurance",
        amount: "0",
        booking_date: "",
      });
      await loadDashboardData();
    } catch {
      setLoadError("Accounting Entry konnte nicht gespeichert werden.");
    }
  }

  async function handleCreateInvoice(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      await createInvoice({
        property_id: invoiceForm.property_id || null,
        vendor_name: invoiceForm.vendor_name,
        invoice_number: invoiceForm.invoice_number || null,
        invoice_date: invoiceForm.invoice_date || null,
        gross_amount: Number(invoiceForm.gross_amount),
        status: invoiceForm.status,
      });
      setInvoiceForm({
        property_id: "",
        vendor_name: "",
        invoice_number: "",
        invoice_date: "",
        gross_amount: "0",
        status: "received",
      });
      await loadDashboardData();
    } catch {
      setLoadError("Rechnung konnte nicht gespeichert werden.");
    }
  }

  async function handleCreatePayment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      await createPayment({
        invoice_id: paymentForm.invoice_id || null,
        contract_id: null,
        amount: Number(paymentForm.amount),
        booking_date: paymentForm.booking_date || null,
        reference: paymentForm.reference || null,
      });
      setPaymentForm({
        invoice_id: "",
        amount: "0",
        booking_date: "",
        reference: "",
      });
      await loadDashboardData();
    } catch {
      setLoadError("Zahlung konnte nicht gespeichert werden.");
    }
  }

  function handleDocumentFileChange(event: ChangeEvent<HTMLInputElement>) {
    setSelectedDocumentFile(event.target.files?.[0] ?? null);
  }

  async function handleUploadDocument(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedDocumentFile || !documentForm.related_id) {
      setLoadError("Bitte Bezug und Datei für den Dokumentenupload auswählen.");
      return;
    }

    setDocumentActionLoading(true);
    setLoadError(null);
    try {
      await uploadDocument({
        related_model: documentForm.related_model,
        related_id: documentForm.related_id,
        document_type: documentForm.document_type,
        file: selectedDocumentFile,
      });
      setSelectedDocumentFile(null);
      setDocumentForm({
        related_model: "invoice",
        related_id: "",
        document_type: "invoice_receipt",
      });
      await loadDashboardData();
    } catch {
      setLoadError("Dokument konnte nicht hochgeladen werden.");
    } finally {
      setDocumentActionLoading(false);
    }
  }

  async function handleProcessDocument(documentId: string) {
    setDocumentActionLoading(true);
    setLoadError(null);
    try {
      await processDocumentOcr(documentId);
      await loadDashboardData();
    } catch {
      setLoadError("OCR-Verarbeitung konnte nicht gestartet werden.");
    } finally {
      setDocumentActionLoading(false);
    }
  }

  async function handleApplyDocumentToInvoice(documentId: string) {
    setDocumentActionLoading(true);
    setLoadError(null);
    try {
      await applyDocumentOcrToInvoice(documentId);
      await loadDashboardData();
    } catch {
      setLoadError("OCR-Daten konnten nicht in die Rechnung übernommen werden.");
    } finally {
      setDocumentActionLoading(false);
    }
  }

  async function handleImportBankTransactions() {
    setBankingActionLoading(true);
    setLoadError(null);
    try {
      await importBankTransactions();
      await loadDashboardData();
    } catch {
      setLoadError("Banktransaktionen konnten nicht importiert werden.");
    } finally {
      setBankingActionLoading(false);
    }
  }

  async function handleMatchBankTransaction(transactionId: string, paymentId: string) {
    if (!paymentId) {
      return;
    }

    setBankingActionLoading(true);
    setLoadError(null);
    try {
      await matchBankTransaction(transactionId, paymentId);
      await loadDashboardData();
    } catch {
      setLoadError("Banktransaktion konnte nicht gematcht werden.");
    } finally {
      setBankingActionLoading(false);
    }
  }

  useEffect(() => {
    if (!isAuthenticated) {
      return;
    }
    void loadDashboardData();
  }, [isAuthenticated]);

  const totalAccountingAmount = useMemo(
    () => entries.reduce((sum, entry) => sum + entry.amount, 0),
    [entries],
  );

  const propertyNameById = useMemo(
    () => new Map(properties.map((property) => [property.id, property.name])),
    [properties],
  );
  const tenantNameById = useMemo(
    () => new Map(tenants.map((tenant) => [tenant.id, formatTenantName(tenant)])),
    [tenants],
  );
  const unitLabelById = useMemo(
    () =>
      new Map(
        units.map((unit) => [
          unit.id,
          `${propertyNameById.get(unit.property_id) ?? "Unbekannte Immobilie"} · ${unit.name}`,
        ]),
      ),
    [propertyNameById, units],
  );
  const invoiceLabelById = useMemo(
    () =>
      new Map(
        invoices.map((invoice) => [
          invoice.id,
          `${invoice.vendor_name} · ${formatCurrency(invoice.gross_amount)}`,
        ]),
      ),
    [invoices],
  );
  const paymentLabelById = useMemo(
    () =>
      new Map(
        payments.map((payment) => [
          payment.id,
          `${formatCurrency(payment.amount)} · ${payment.reference ?? payment.id}`,
        ]),
      ),
    [payments],
  );

  const propertyOptions = properties.map((property) => ({
    value: property.id,
    label: property.name,
  }));
  const unitOptions = units.map((unit) => ({
    value: unit.id,
    label: unitLabelById.get(unit.id) ?? unit.name,
  }));
  const tenantOptions = tenants.map((tenant) => ({
    value: tenant.id,
    label: formatTenantName(tenant),
  }));
  const invoiceOptions = invoices.map((invoice) => ({
    value: invoice.id,
    label: invoiceLabelById.get(invoice.id) ?? invoice.vendor_name,
  }));
  const documentTargetOptions =
    documentForm.related_model === "property" ? propertyOptions : invoiceOptions;

  const filteredProperties = useMemo(
    () =>
      properties.filter((property) =>
        matchesSearch(propertyList.search, [
          property.name,
          property.property_type,
          property.street,
          property.city,
          property.postal_code,
        ]),
      ),
    [properties, propertyList.search],
  );

  const filteredUnits = useMemo(
    () =>
      units.filter((unit) => {
        const matchesProperty =
          unitList.property_id === "all" || unit.property_id === unitList.property_id;
        const matchesStatus = unitList.status === "all" || unit.status === unitList.status;
        const matchesUnitSearch = matchesSearch(unitList.search, [
          unit.name,
          unit.unit_type,
          unit.status,
          propertyNameById.get(unit.property_id),
          unit.area_sqm,
        ]);
        return matchesProperty && matchesStatus && matchesUnitSearch;
      }),
    [propertyNameById, unitList.property_id, unitList.search, unitList.status, units],
  );

  const filteredTenants = useMemo(
    () =>
      tenants.filter((tenant) =>
        matchesSearch(tenantList.search, [
          tenant.first_name,
          tenant.last_name,
          tenant.email,
          tenant.phone,
        ]),
      ),
    [tenantList.search, tenants],
  );

  const filteredContracts = useMemo(
    () =>
      contracts.filter((contract) => {
        const matchesUnit =
          contractList.unit_id === "all" || contract.unit_id === contractList.unit_id;
        const matchesTenant =
          contractList.tenant_id === "all" || contract.tenant_id === contractList.tenant_id;
        const matchesContractSearch = matchesSearch(contractList.search, [
          unitLabelById.get(contract.unit_id),
          tenantNameById.get(contract.tenant_id),
          contract.start_date,
          contract.end_date,
          contract.cold_rent,
        ]);
        return matchesUnit && matchesTenant && matchesContractSearch;
      }),
    [
      contractList.search,
      contractList.tenant_id,
      contractList.unit_id,
      contracts,
      tenantNameById,
      unitLabelById,
    ],
  );

  const filteredInvoices = useMemo(
    () =>
      invoices.filter((invoice) => {
        const matchesStatus =
          invoiceList.status === "all" || invoice.status === invoiceList.status;
        const matchesInvoiceSearch = matchesSearch(invoiceList.search, [
          invoice.vendor_name,
          invoice.invoice_number,
          invoice.status,
          invoice.invoice_date,
          propertyNameById.get(invoice.property_id ?? ""),
          invoice.gross_amount,
        ]);
        return matchesStatus && matchesInvoiceSearch;
      }),
    [invoiceList.search, invoiceList.status, invoices, propertyNameById],
  );

  const filteredPayments = useMemo(
    () =>
      payments.filter((payment) =>
        matchesSearch(paymentList.search, [
          payment.reference,
          payment.booking_date,
          payment.amount,
          invoiceLabelById.get(payment.invoice_id ?? ""),
        ]),
      ),
    [invoiceLabelById, paymentList.search, payments],
  );

  const filteredBankTransactions = useMemo(
    () =>
      bankTransactions.filter((transaction) => {
        const matchesStatus =
          bankTransactionList.status === "all" ||
          transaction.status === bankTransactionList.status;
        const matchesBankSearch = matchesSearch(bankTransactionList.search, [
          transaction.account_name,
          transaction.counterparty_name,
          transaction.reference,
          transaction.iban,
          transaction.amount,
          transaction.currency,
        ]);
        return matchesStatus && matchesBankSearch;
      }),
    [bankTransactionList.search, bankTransactionList.status, bankTransactions],
  );

  const filteredDocuments = useMemo(
    () =>
      documents.filter((document) => {
        const matchesStatus =
          documentList.ocr_status === "all" || document.ocr_status === documentList.ocr_status;
        const matchesModel =
          documentList.related_model === "all" ||
          document.related_model === documentList.related_model;
        const matchesDocumentSearch = matchesSearch(documentList.search, [
          document.file_name,
          document.document_type,
          document.related_model,
          document.ocr_result?.vendor_name,
          document.ocr_result?.invoice_number,
          document.ocr_result?.gross_amount,
        ]);
        return matchesStatus && matchesModel && matchesDocumentSearch;
      }),
    [documentList.ocr_status, documentList.related_model, documentList.search, documents],
  );

  const pageTitles: Record<AppRoute, { title: string; subtitle: string }> = {
    overview: {
      title: "Immobilienverwaltung Dashboard",
      subtitle: "Zentrale Übersicht über Kennzahlen, Portfolio und letzte Vorgänge.",
    },
    properties: {
      title: "Immobilien",
      subtitle: "Objekte erfassen, durchsuchen und als Stammdatenbasis pflegen.",
    },
    units: {
      title: "Wohneinheiten",
      subtitle: "Einheiten nach Immobilie strukturieren und Belegungsstatus pflegen.",
    },
    tenants: {
      title: "Mieter",
      subtitle: "Mieterprofile mit Kontaktdaten und Einzugsdaten verwalten.",
    },
    contracts: {
      title: "Verträge",
      subtitle: "Mietverträge zwischen Einheit und Mieter pflegen.",
    },
    accounting: {
      title: "Accounting",
      subtitle: "Buchungssätze erfassen und die letzten Accounting Entries prüfen.",
    },
    billing: {
      title: "Billing",
      subtitle: "Rechnungen und Zahlungen mit Suche und Pagination verwalten.",
    },
    banking: {
      title: "Banking",
      subtitle: "Kontoereignisse importieren, filtern und Zahlungen zuordnen.",
    },
    documents: {
      title: "Dokumente & OCR",
      subtitle: "Belege hochladen, filtern und OCR-Ergebnisse auf Rechnungen anwenden.",
    },
  };

  if (!isAuthenticated) {
    return (
      <Stack spacing={3}>
        <div>
          <Typography variant="h4" gutterBottom>
            PropertyHub Dashboard
          </Typography>
          <Typography color="text.secondary">
            Frontend-MVP mit Login, Stammdaten, Billing, Banking und Dokumentenworkflow.
          </Typography>
        </div>

        <Alert severity="info">
          Melde dich mit dem Bootstrap-Admin aus der Backend-Konfiguration an.
        </Alert>

        <Card>
          <CardContent>
            <Stack component="form" spacing={2} onSubmit={handleLogin}>
              <TextField
                label="E-Mail"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
              />
              <TextField
                label="Passwort"
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
              />
              {loginError ? <Alert severity="error">{loginError}</Alert> : null}
              <Box>
                <Button type="submit" variant="contained">
                  Login
                </Button>
              </Box>
            </Stack>
          </CardContent>
        </Card>
      </Stack>
    );
  }

  if (isLoadingUser || !currentUser) {
    return <Alert severity="info">Benutzerprofil wird geladen...</Alert>;
  }

  const kpis = [
    { label: "Immobilien", value: String(report?.properties_count ?? properties.length) },
    { label: "Einheiten", value: String(report?.units_count ?? units.length) },
    { label: "Mieter", value: String(report?.tenants_count ?? tenants.length) },
    { label: "Verträge", value: String(report?.contracts_count ?? contracts.length) },
    { label: "Rechnungen offen", value: String(report?.open_invoices_count ?? 0) },
    { label: "Zahlungen", value: String(report?.payments_count ?? payments.length) },
    { label: "Banktransaktionen", value: String(bankTransactions.length) },
    { label: "Dokumente", value: String(documents.length) },
    {
      label: "Accounting Gesamt",
      value: formatCurrency(report?.total_expense_amount ?? totalAccountingAmount),
    },
  ];
  const pageTitle = pageTitles[currentRoute];

  return (
    <Stack spacing={3}>
      <div>
        <Typography variant="h4" gutterBottom>
          {pageTitle.title}
        </Typography>
        <Typography color="text.secondary">{pageTitle.subtitle}</Typography>
      </div>

      {loadError ? <Alert severity="error">{loadError}</Alert> : null}
      {loading ? <Alert severity="info">Daten werden geladen...</Alert> : null}
      {!canManageData ? (
        <Alert severity="info">
          Deine Rolle ist aktuell read-only. Listen und Auswertungen bleiben sichtbar, Änderungen
          sind gesperrt.
        </Alert>
      ) : null}

      {currentRoute === "overview" ? (
        <>
          <Grid container spacing={2}>
            {kpis.map((kpi) => (
              <Grid key={kpi.label} item xs={12} sm={6} md={4}>
                <Card>
                  <CardContent>
                    <Typography color="text.secondary" variant="body2">
                      {kpi.label}
                    </Typography>
                    <Typography variant="h5" sx={{ mt: 1 }}>
                      {kpi.value}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>

          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Portfolio
                  </Typography>
                  <List dense>
                    {properties.slice(0, 5).map((property) => (
                      <ListItem key={property.id} disableGutters>
                        <ListItemText
                          primary={property.name}
                          secondary={`${property.property_type} · ${formatPropertyLocation(property)}`}
                        />
                      </ListItem>
                    ))}
                    {!properties.length ? (
                      <Typography color="text.secondary">
                        Noch keine Immobilien vorhanden.
                      </Typography>
                    ) : null}
                  </List>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Letzte Verträge
                  </Typography>
                  <List dense>
                    {contracts.slice(0, 5).map((contract) => (
                      <ListItem key={contract.id} disableGutters>
                        <ListItemText
                          primary={`${tenantNameById.get(contract.tenant_id) ?? "Unbekannter Mieter"} · ${formatCurrency(contract.cold_rent)}`}
                          secondary={`${unitLabelById.get(contract.unit_id) ?? "Unbekannte Einheit"} · Start ${contract.start_date}`}
                        />
                      </ListItem>
                    ))}
                    {!contracts.length ? (
                      <Typography color="text.secondary">
                        Noch keine Verträge vorhanden.
                      </Typography>
                    ) : null}
                  </List>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Letzte Rechnungen
                  </Typography>
                  <List dense>
                    {invoices.slice(0, 5).map((invoice) => (
                      <ListItem key={invoice.id} disableGutters>
                        <ListItemText
                          primary={`${invoice.vendor_name} · ${formatCurrency(invoice.gross_amount)}`}
                          secondary={`${invoice.status} · ${invoice.invoice_date ?? "-"}`}
                        />
                      </ListItem>
                    ))}
                    {!invoices.length ? (
                      <Typography color="text.secondary">
                        Noch keine Rechnungen vorhanden.
                      </Typography>
                    ) : null}
                  </List>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Letzte Dokumente
                  </Typography>
                  <List dense>
                    {documents.slice(0, 5).map((document) => (
                      <ListItem key={document.id} disableGutters>
                        <ListItemText
                          primary={document.file_name}
                          secondary={`${document.related_model} · OCR ${document.ocr_status}`}
                        />
                      </ListItem>
                    ))}
                    {!documents.length ? (
                      <Typography color="text.secondary">
                        Noch keine Dokumente vorhanden.
                      </Typography>
                    ) : null}
                  </List>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </>
      ) : null}

      {currentRoute === "properties" ? (
        <Grid container spacing={2}>
          {canManageData ? (
            <Grid item xs={12} md={5}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Immobilie anlegen
                  </Typography>
                  <Stack component="form" spacing={2} onSubmit={handleCreateProperty}>
                    <TextField
                      label="Name"
                      value={propertyForm.name}
                      onChange={(event) =>
                        setPropertyForm((current) => ({ ...current, name: event.target.value }))
                      }
                    />
                    <TextField
                      select
                      label="Typ"
                      value={propertyForm.property_type}
                      onChange={(event) =>
                        setPropertyForm((current) => ({
                          ...current,
                          property_type: event.target.value,
                        }))
                      }
                    >
                      <MenuItem value="residential">Residential</MenuItem>
                      <MenuItem value="commercial">Commercial</MenuItem>
                      <MenuItem value="parking">Parking</MenuItem>
                    </TextField>
                    <TextField
                      label="Straße"
                      value={propertyForm.street}
                      onChange={(event) =>
                        setPropertyForm((current) => ({ ...current, street: event.target.value }))
                      }
                    />
                    <TextField
                      label="Stadt"
                      value={propertyForm.city}
                      onChange={(event) =>
                        setPropertyForm((current) => ({ ...current, city: event.target.value }))
                      }
                    />
                    <TextField
                      label="PLZ"
                      value={propertyForm.postal_code}
                      onChange={(event) =>
                        setPropertyForm((current) => ({
                          ...current,
                          postal_code: event.target.value,
                        }))
                      }
                    />
                    <TextField
                      label="Kaufpreis"
                      type="number"
                      value={propertyForm.purchase_price}
                      onChange={(event) =>
                        setPropertyForm((current) => ({
                          ...current,
                          purchase_price: event.target.value,
                        }))
                      }
                    />
                    <Box>
                      <Button type="submit" variant="contained">
                        Immobilie speichern
                      </Button>
                    </Box>
                  </Stack>
                </CardContent>
              </Card>
            </Grid>
          ) : null}

          <Grid item xs={12} md={canManageData ? 7 : 12}>
            <ManagedListCard
              title="Immobilienbestand"
              items={filteredProperties}
              emptyText="Noch keine Immobilien vorhanden."
              searchValue={propertyList.search}
              onSearchChange={(value) =>
                setPropertyList((current) => ({ ...current, search: value, page: 1 }))
              }
              page={propertyList.page}
              onPageChange={(page) =>
                setPropertyList((current) => ({
                  ...current,
                  page,
                }))
              }
              pageSize={propertyList.pageSize}
              onPageSizeChange={(pageSize) =>
                setPropertyList((current) => ({ ...current, pageSize, page: 1 }))
              }
              searchLabel="Name, Ort oder Adresse"
              renderPrimary={(property) => property.name}
              renderSecondary={(property) =>
                `${property.property_type} · ${formatPropertyLocation(property)}`
              }
              renderDetails={(property) => (
                <Typography color="text.secondary" variant="body2">
                  Kaufpreis: {formatCurrency(property.purchase_price)}
                </Typography>
              )}
            />
          </Grid>
        </Grid>
      ) : null}

      {currentRoute === "units" ? (
        <Grid container spacing={2}>
          {canManageData ? (
            <Grid item xs={12} md={5}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Einheit anlegen
                  </Typography>
                  <Stack component="form" spacing={2} onSubmit={handleCreateUnit}>
                    <TextField
                      select
                      label="Immobilie"
                      value={unitForm.property_id}
                      onChange={(event) =>
                        setUnitForm((current) => ({
                          ...current,
                          property_id: event.target.value,
                        }))
                      }
                    >
                      <MenuItem value="">Immobilie wählen</MenuItem>
                      {propertyOptions.map((option) => (
                        <MenuItem key={option.value} value={option.value}>
                          {option.label}
                        </MenuItem>
                      ))}
                    </TextField>
                    <TextField
                      label="Einheitsname"
                      value={unitForm.name}
                      onChange={(event) =>
                        setUnitForm((current) => ({ ...current, name: event.target.value }))
                      }
                    />
                    <TextField
                      select
                      label="Typ"
                      value={unitForm.unit_type}
                      onChange={(event) =>
                        setUnitForm((current) => ({
                          ...current,
                          unit_type: event.target.value,
                        }))
                      }
                    >
                      <MenuItem value="apartment">Apartment</MenuItem>
                      <MenuItem value="commercial">Commercial</MenuItem>
                      <MenuItem value="garage">Garage</MenuItem>
                    </TextField>
                    <TextField
                      select
                      label="Status"
                      value={unitForm.status}
                      onChange={(event) =>
                        setUnitForm((current) => ({ ...current, status: event.target.value }))
                      }
                    >
                      <MenuItem value="vacant">Vacant</MenuItem>
                      <MenuItem value="occupied">Occupied</MenuItem>
                      <MenuItem value="reserved">Reserved</MenuItem>
                    </TextField>
                    <TextField
                      label="Fläche (qm)"
                      type="number"
                      value={unitForm.area_sqm}
                      onChange={(event) =>
                        setUnitForm((current) => ({ ...current, area_sqm: event.target.value }))
                      }
                    />
                    <Box>
                      <Button type="submit" variant="contained">
                        Einheit speichern
                      </Button>
                    </Box>
                  </Stack>
                </CardContent>
              </Card>
            </Grid>
          ) : null}

          <Grid item xs={12} md={canManageData ? 7 : 12}>
            <ManagedListCard
              title="Einheiten"
              items={filteredUnits}
              emptyText="Noch keine Einheiten vorhanden."
              searchValue={unitList.search}
              onSearchChange={(value) =>
                setUnitList((current) => ({ ...current, search: value, page: 1 }))
              }
              page={unitList.page}
              onPageChange={(page) =>
                setUnitList((current) => ({
                  ...current,
                  page,
                }))
              }
              pageSize={unitList.pageSize}
              onPageSizeChange={(pageSize) =>
                setUnitList((current) => ({ ...current, pageSize, page: 1 }))
              }
              searchLabel="Einheit, Immobilie oder Typ"
              extraFilters={
                <>
                  <TextField
                    select
                    size="small"
                    label="Immobilie"
                    value={unitList.property_id}
                    onChange={(event) =>
                      setUnitList((current) => ({
                        ...current,
                        property_id: event.target.value,
                        page: 1,
                      }))
                    }
                    sx={{ minWidth: 180 }}
                  >
                    <MenuItem value="all">Alle Immobilien</MenuItem>
                    {propertyOptions.map((option) => (
                      <MenuItem key={option.value} value={option.value}>
                        {option.label}
                      </MenuItem>
                    ))}
                  </TextField>
                  <TextField
                    select
                    size="small"
                    label="Status"
                    value={unitList.status}
                    onChange={(event) =>
                      setUnitList((current) => ({
                        ...current,
                        status: event.target.value,
                        page: 1,
                      }))
                    }
                    sx={{ minWidth: 140 }}
                  >
                    <MenuItem value="all">Alle Stati</MenuItem>
                    <MenuItem value="vacant">Vacant</MenuItem>
                    <MenuItem value="occupied">Occupied</MenuItem>
                    <MenuItem value="reserved">Reserved</MenuItem>
                  </TextField>
                </>
              }
              renderPrimary={(unit) => unit.name}
              renderSecondary={(unit) =>
                `${propertyNameById.get(unit.property_id) ?? "Unbekannte Immobilie"} · ${unit.unit_type} · ${unit.status}`
              }
              renderDetails={(unit) => (
                <Typography color="text.secondary" variant="body2">
                  Fläche: {unit.area_sqm ? `${unit.area_sqm} qm` : "-"}
                </Typography>
              )}
            />
          </Grid>
        </Grid>
      ) : null}

      {currentRoute === "tenants" ? (
        <Grid container spacing={2}>
          {canManageData ? (
            <Grid item xs={12} md={5}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Mieter anlegen
                  </Typography>
                  <Stack component="form" spacing={2} onSubmit={handleCreateTenant}>
                    <TextField
                      label="Vorname"
                      value={tenantForm.first_name}
                      onChange={(event) =>
                        setTenantForm((current) => ({
                          ...current,
                          first_name: event.target.value,
                        }))
                      }
                    />
                    <TextField
                      label="Nachname"
                      value={tenantForm.last_name}
                      onChange={(event) =>
                        setTenantForm((current) => ({
                          ...current,
                          last_name: event.target.value,
                        }))
                      }
                    />
                    <TextField
                      label="E-Mail"
                      value={tenantForm.email}
                      onChange={(event) =>
                        setTenantForm((current) => ({ ...current, email: event.target.value }))
                      }
                    />
                    <TextField
                      label="Telefon"
                      value={tenantForm.phone}
                      onChange={(event) =>
                        setTenantForm((current) => ({ ...current, phone: event.target.value }))
                      }
                    />
                    <TextField
                      label="Einzug"
                      type="date"
                      value={tenantForm.move_in_date}
                      onChange={(event) =>
                        setTenantForm((current) => ({
                          ...current,
                          move_in_date: event.target.value,
                        }))
                      }
                      InputLabelProps={{ shrink: true }}
                    />
                    <TextField
                      label="Auszug"
                      type="date"
                      value={tenantForm.move_out_date}
                      onChange={(event) =>
                        setTenantForm((current) => ({
                          ...current,
                          move_out_date: event.target.value,
                        }))
                      }
                      InputLabelProps={{ shrink: true }}
                    />
                    <Box>
                      <Button type="submit" variant="contained">
                        Mieter speichern
                      </Button>
                    </Box>
                  </Stack>
                </CardContent>
              </Card>
            </Grid>
          ) : null}

          <Grid item xs={12} md={canManageData ? 7 : 12}>
            <ManagedListCard
              title="Mieterbestand"
              items={filteredTenants}
              emptyText="Noch keine Mieter vorhanden."
              searchValue={tenantList.search}
              onSearchChange={(value) =>
                setTenantList((current) => ({ ...current, search: value, page: 1 }))
              }
              page={tenantList.page}
              onPageChange={(page) =>
                setTenantList((current) => ({
                  ...current,
                  page,
                }))
              }
              pageSize={tenantList.pageSize}
              onPageSizeChange={(pageSize) =>
                setTenantList((current) => ({ ...current, pageSize, page: 1 }))
              }
              searchLabel="Name, E-Mail oder Telefon"
              renderPrimary={(tenant) => formatTenantName(tenant)}
              renderSecondary={(tenant) => tenant.email ?? "Keine E-Mail"}
              renderDetails={(tenant) => (
                <Typography color="text.secondary" variant="body2">
                  Telefon: {tenant.phone ?? "-"} · Einzug: {tenant.move_in_date ?? "-"} · Auszug:{" "}
                  {tenant.move_out_date ?? "-"}
                </Typography>
              )}
            />
          </Grid>
        </Grid>
      ) : null}

      {currentRoute === "contracts" ? (
        <Grid container spacing={2}>
          {canManageData ? (
            <Grid item xs={12} md={5}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Vertrag anlegen
                  </Typography>
                  <Stack component="form" spacing={2} onSubmit={handleCreateContract}>
                    <TextField
                      select
                      label="Einheit"
                      value={contractForm.unit_id}
                      onChange={(event) =>
                        setContractForm((current) => ({
                          ...current,
                          unit_id: event.target.value,
                        }))
                      }
                    >
                      <MenuItem value="">Einheit wählen</MenuItem>
                      {unitOptions.map((option) => (
                        <MenuItem key={option.value} value={option.value}>
                          {option.label}
                        </MenuItem>
                      ))}
                    </TextField>
                    <TextField
                      select
                      label="Mieter"
                      value={contractForm.tenant_id}
                      onChange={(event) =>
                        setContractForm((current) => ({
                          ...current,
                          tenant_id: event.target.value,
                        }))
                      }
                    >
                      <MenuItem value="">Mieter wählen</MenuItem>
                      {tenantOptions.map((option) => (
                        <MenuItem key={option.value} value={option.value}>
                          {option.label}
                        </MenuItem>
                      ))}
                    </TextField>
                    <TextField
                      label="Startdatum"
                      type="date"
                      value={contractForm.start_date}
                      onChange={(event) =>
                        setContractForm((current) => ({
                          ...current,
                          start_date: event.target.value,
                        }))
                      }
                      InputLabelProps={{ shrink: true }}
                    />
                    <TextField
                      label="Enddatum"
                      type="date"
                      value={contractForm.end_date}
                      onChange={(event) =>
                        setContractForm((current) => ({
                          ...current,
                          end_date: event.target.value,
                        }))
                      }
                      InputLabelProps={{ shrink: true }}
                    />
                    <TextField
                      label="Kaltmiete"
                      type="number"
                      value={contractForm.cold_rent}
                      onChange={(event) =>
                        setContractForm((current) => ({
                          ...current,
                          cold_rent: event.target.value,
                        }))
                      }
                    />
                    <TextField
                      label="Nebenkosten-Vorauszahlung"
                      type="number"
                      value={contractForm.service_charge_advance}
                      onChange={(event) =>
                        setContractForm((current) => ({
                          ...current,
                          service_charge_advance: event.target.value,
                        }))
                      }
                    />
                    <Box>
                      <Button type="submit" variant="contained">
                        Vertrag speichern
                      </Button>
                    </Box>
                  </Stack>
                </CardContent>
              </Card>
            </Grid>
          ) : null}

          <Grid item xs={12} md={canManageData ? 7 : 12}>
            <ManagedListCard
              title="Verträge"
              items={filteredContracts}
              emptyText="Noch keine Verträge vorhanden."
              searchValue={contractList.search}
              onSearchChange={(value) =>
                setContractList((current) => ({ ...current, search: value, page: 1 }))
              }
              page={contractList.page}
              onPageChange={(page) =>
                setContractList((current) => ({
                  ...current,
                  page,
                }))
              }
              pageSize={contractList.pageSize}
              onPageSizeChange={(pageSize) =>
                setContractList((current) => ({ ...current, pageSize, page: 1 }))
              }
              searchLabel="Einheit, Mieter oder Startdatum"
              extraFilters={
                <>
                  <TextField
                    select
                    size="small"
                    label="Einheit"
                    value={contractList.unit_id}
                    onChange={(event) =>
                      setContractList((current) => ({
                        ...current,
                        unit_id: event.target.value,
                        page: 1,
                      }))
                    }
                    sx={{ minWidth: 180 }}
                  >
                    <MenuItem value="all">Alle Einheiten</MenuItem>
                    {unitOptions.map((option) => (
                      <MenuItem key={option.value} value={option.value}>
                        {option.label}
                      </MenuItem>
                    ))}
                  </TextField>
                  <TextField
                    select
                    size="small"
                    label="Mieter"
                    value={contractList.tenant_id}
                    onChange={(event) =>
                      setContractList((current) => ({
                        ...current,
                        tenant_id: event.target.value,
                        page: 1,
                      }))
                    }
                    sx={{ minWidth: 180 }}
                  >
                    <MenuItem value="all">Alle Mieter</MenuItem>
                    {tenantOptions.map((option) => (
                      <MenuItem key={option.value} value={option.value}>
                        {option.label}
                      </MenuItem>
                    ))}
                  </TextField>
                </>
              }
              renderPrimary={(contract) =>
                `${tenantNameById.get(contract.tenant_id) ?? "Unbekannter Mieter"} · ${formatCurrency(contract.cold_rent)}`
              }
              renderSecondary={(contract) =>
                `${unitLabelById.get(contract.unit_id) ?? "Unbekannte Einheit"} · ${contract.start_date} bis ${contract.end_date ?? "offen"}`
              }
              renderDetails={(contract) => (
                <Typography color="text.secondary" variant="body2">
                  Nebenkosten-Vorauszahlung: {formatCurrency(contract.service_charge_advance)}
                </Typography>
              )}
            />
          </Grid>
        </Grid>
      ) : null}

      {currentRoute === "accounting" ? (
        <Grid container spacing={2}>
          {canManageData ? (
            <Grid item xs={12} md={5}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Accounting Entry anlegen
                  </Typography>
                  <Stack component="form" spacing={2} onSubmit={handleCreateEntry}>
                    <TextField
                      select
                      label="Immobilie"
                      value={entryForm.property_id}
                      onChange={(event) =>
                        setEntryForm((current) => ({
                          ...current,
                          property_id: event.target.value,
                        }))
                      }
                    >
                      <MenuItem value="">Ohne Immobilie</MenuItem>
                      {propertyOptions.map((option) => (
                        <MenuItem key={option.value} value={option.value}>
                          {option.label}
                        </MenuItem>
                      ))}
                    </TextField>
                    <TextField
                      select
                      label="Typ"
                      value={entryForm.entry_type}
                      onChange={(event) =>
                        setEntryForm((current) => ({
                          ...current,
                          entry_type: event.target.value,
                        }))
                      }
                    >
                      <MenuItem value="expense">Expense</MenuItem>
                      <MenuItem value="income">Income</MenuItem>
                    </TextField>
                    <TextField
                      label="Kategorie"
                      value={entryForm.category}
                      onChange={(event) =>
                        setEntryForm((current) => ({
                          ...current,
                          category: event.target.value,
                        }))
                      }
                    />
                    <TextField
                      label="Betrag"
                      type="number"
                      value={entryForm.amount}
                      onChange={(event) =>
                        setEntryForm((current) => ({
                          ...current,
                          amount: event.target.value,
                        }))
                      }
                    />
                    <TextField
                      label="Buchungsdatum"
                      type="date"
                      value={entryForm.booking_date}
                      onChange={(event) =>
                        setEntryForm((current) => ({
                          ...current,
                          booking_date: event.target.value,
                        }))
                      }
                      InputLabelProps={{ shrink: true }}
                    />
                    <Box>
                      <Button type="submit" variant="contained">
                        Entry speichern
                      </Button>
                    </Box>
                  </Stack>
                </CardContent>
              </Card>
            </Grid>
          ) : null}
          <Grid item xs={12} md={canManageData ? 7 : 12}>
            <ManagedListCard
              title="Letzte Buchungssätze"
              items={entries}
              emptyText="Noch keine Accounting Entries vorhanden."
              searchValue=""
              onSearchChange={() => undefined}
              page={1}
              onPageChange={() => undefined}
              pageSize={10}
              onPageSizeChange={() => undefined}
              helperText="Accounting bleibt vorerst als Schnellübersicht ohne erweiterte Filterlogik."
              renderPrimary={(entry) =>
                `${entry.entry_type} · ${formatCurrency(entry.amount)}`
              }
              renderSecondary={(entry) =>
                `${entry.category ?? "-"} · ${entry.booking_date ?? "-"}`
              }
            />
          </Grid>
        </Grid>
      ) : null}

      {currentRoute === "billing" ? (
        <>
          {canManageData ? (
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Rechnung anlegen
                    </Typography>
                    <Stack component="form" spacing={2} onSubmit={handleCreateInvoice}>
                      <TextField
                        select
                        label="Immobilie"
                        value={invoiceForm.property_id}
                        onChange={(event) =>
                          setInvoiceForm((current) => ({
                            ...current,
                            property_id: event.target.value,
                          }))
                        }
                      >
                        <MenuItem value="">Ohne Immobilie</MenuItem>
                        {propertyOptions.map((option) => (
                          <MenuItem key={option.value} value={option.value}>
                            {option.label}
                          </MenuItem>
                        ))}
                      </TextField>
                      <TextField
                        label="Lieferant"
                        value={invoiceForm.vendor_name}
                        onChange={(event) =>
                          setInvoiceForm((current) => ({
                            ...current,
                            vendor_name: event.target.value,
                          }))
                        }
                      />
                      <TextField
                        label="Rechnungsnummer"
                        value={invoiceForm.invoice_number}
                        onChange={(event) =>
                          setInvoiceForm((current) => ({
                            ...current,
                            invoice_number: event.target.value,
                          }))
                        }
                      />
                      <TextField
                        label="Rechnungsdatum"
                        type="date"
                        value={invoiceForm.invoice_date}
                        onChange={(event) =>
                          setInvoiceForm((current) => ({
                            ...current,
                            invoice_date: event.target.value,
                          }))
                        }
                        InputLabelProps={{ shrink: true }}
                      />
                      <TextField
                        label="Betrag"
                        type="number"
                        value={invoiceForm.gross_amount}
                        onChange={(event) =>
                          setInvoiceForm((current) => ({
                            ...current,
                            gross_amount: event.target.value,
                          }))
                        }
                      />
                      <TextField
                        select
                        label="Status"
                        value={invoiceForm.status}
                        onChange={(event) =>
                          setInvoiceForm((current) => ({
                            ...current,
                            status: event.target.value,
                          }))
                        }
                      >
                        <MenuItem value="draft">Draft</MenuItem>
                        <MenuItem value="received">Received</MenuItem>
                        <MenuItem value="approved">Approved</MenuItem>
                        <MenuItem value="paid">Paid</MenuItem>
                      </TextField>
                      <Box>
                        <Button type="submit" variant="contained">
                          Rechnung speichern
                        </Button>
                      </Box>
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Zahlung anlegen
                    </Typography>
                    <Stack component="form" spacing={2} onSubmit={handleCreatePayment}>
                      <TextField
                        select
                        label="Rechnung"
                        value={paymentForm.invoice_id}
                        onChange={(event) =>
                          setPaymentForm((current) => ({
                            ...current,
                            invoice_id: event.target.value,
                          }))
                        }
                      >
                        <MenuItem value="">Rechnung wählen</MenuItem>
                        {invoiceOptions.map((option) => (
                          <MenuItem key={option.value} value={option.value}>
                            {option.label}
                          </MenuItem>
                        ))}
                      </TextField>
                      <TextField
                        label="Betrag"
                        type="number"
                        value={paymentForm.amount}
                        onChange={(event) =>
                          setPaymentForm((current) => ({
                            ...current,
                            amount: event.target.value,
                          }))
                        }
                      />
                      <TextField
                        label="Buchungsdatum"
                        type="date"
                        value={paymentForm.booking_date}
                        onChange={(event) =>
                          setPaymentForm((current) => ({
                            ...current,
                            booking_date: event.target.value,
                          }))
                        }
                        InputLabelProps={{ shrink: true }}
                      />
                      <TextField
                        label="Referenz"
                        value={paymentForm.reference}
                        onChange={(event) =>
                          setPaymentForm((current) => ({
                            ...current,
                            reference: event.target.value,
                          }))
                        }
                      />
                      <Box>
                        <Button type="submit" variant="contained">
                          Zahlung speichern
                        </Button>
                      </Box>
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          ) : null}

          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <ManagedListCard
                title="Rechnungen"
                items={filteredInvoices}
                emptyText="Noch keine Rechnungen vorhanden."
                searchValue={invoiceList.search}
                onSearchChange={(value) =>
                  setInvoiceList((current) => ({ ...current, search: value, page: 1 }))
                }
                page={invoiceList.page}
                onPageChange={(page) =>
                  setInvoiceList((current) => ({
                    ...current,
                    page,
                  }))
                }
                pageSize={invoiceList.pageSize}
                onPageSizeChange={(pageSize) =>
                  setInvoiceList((current) => ({ ...current, pageSize, page: 1 }))
                }
                searchLabel="Lieferant, Nummer oder Immobilie"
                extraFilters={
                  <TextField
                    select
                    size="small"
                    label="Status"
                    value={invoiceList.status}
                    onChange={(event) =>
                      setInvoiceList((current) => ({
                        ...current,
                        status: event.target.value,
                        page: 1,
                      }))
                    }
                    sx={{ minWidth: 150 }}
                  >
                    <MenuItem value="all">Alle Stati</MenuItem>
                    <MenuItem value="draft">Draft</MenuItem>
                    <MenuItem value="received">Received</MenuItem>
                    <MenuItem value="approved">Approved</MenuItem>
                    <MenuItem value="paid">Paid</MenuItem>
                  </TextField>
                }
                renderPrimary={(invoice) =>
                  `${invoice.vendor_name} · ${formatCurrency(invoice.gross_amount)}`
                }
                renderSecondary={(invoice) =>
                  `${invoice.status} · ${invoice.invoice_date ?? "-"} · ${propertyNameById.get(invoice.property_id ?? "") ?? "Ohne Immobilie"}`
                }
                renderDetails={(invoice) => (
                  <Typography color="text.secondary" variant="body2">
                    Rechnungsnummer: {invoice.invoice_number ?? "-"}
                  </Typography>
                )}
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <ManagedListCard
                title="Zahlungen"
                items={filteredPayments}
                emptyText="Noch keine Zahlungen vorhanden."
                searchValue={paymentList.search}
                onSearchChange={(value) =>
                  setPaymentList((current) => ({ ...current, search: value, page: 1 }))
                }
                page={paymentList.page}
                onPageChange={(page) =>
                  setPaymentList((current) => ({
                    ...current,
                    page,
                  }))
                }
                pageSize={paymentList.pageSize}
                onPageSizeChange={(pageSize) =>
                  setPaymentList((current) => ({ ...current, pageSize, page: 1 }))
                }
                searchLabel="Referenz, Datum oder Rechnung"
                renderPrimary={(payment) => formatCurrency(payment.amount)}
                renderSecondary={(payment) =>
                  `${payment.reference ?? "-"} · ${payment.booking_date ?? "-"}`
                }
                renderDetails={(payment) => (
                  <Typography color="text.secondary" variant="body2">
                    Zugeordnete Rechnung:{" "}
                    {payment.invoice_id ? invoiceLabelById.get(payment.invoice_id) ?? payment.invoice_id : "-"}
                  </Typography>
                )}
              />
            </Grid>
          </Grid>
        </>
      ) : null}

      {currentRoute === "banking" ? (
        <ManagedListCard
          title="Banking & Matching"
          items={filteredBankTransactions}
          emptyText="Noch keine Banktransaktionen vorhanden."
          searchValue={bankTransactionList.search}
          onSearchChange={(value) =>
            setBankTransactionList((current) => ({ ...current, search: value, page: 1 }))
          }
          page={bankTransactionList.page}
          onPageChange={(page) =>
            setBankTransactionList((current) => ({
              ...current,
              page,
            }))
          }
          pageSize={bankTransactionList.pageSize}
          onPageSizeChange={(pageSize) =>
            setBankTransactionList((current) => ({ ...current, pageSize, page: 1 }))
          }
          searchLabel="Gegenpartei, Referenz oder IBAN"
          helperText="Import und Matching sind noch stub-basiert, aber Suche, Statusfilter und Seitennavigation sind nun vereinheitlicht."
          extraFilters={
            <>
              <TextField
                select
                size="small"
                label="Status"
                value={bankTransactionList.status}
                onChange={(event) =>
                  setBankTransactionList((current) => ({
                    ...current,
                    status: event.target.value,
                    page: 1,
                  }))
                }
                sx={{ minWidth: 150 }}
              >
                <MenuItem value="all">Alle Stati</MenuItem>
                <MenuItem value="imported">Imported</MenuItem>
                <MenuItem value="matched">Matched</MenuItem>
              </TextField>
              {canManageData ? (
                <Button
                  variant="contained"
                  onClick={() => void handleImportBankTransactions()}
                  disabled={bankingActionLoading}
                >
                  Import-Stub ausführen
                </Button>
              ) : null}
            </>
          }
          renderPrimary={(transaction) =>
            `${formatCurrency(transaction.amount)} ${transaction.currency} · ${transaction.counterparty_name ?? transaction.account_name}`
          }
          renderSecondary={(transaction) =>
            `${transaction.reference ?? "-"} · ${transaction.booking_date ?? "-"} · Status: ${transaction.status}`
          }
          renderDetails={(transaction) => (
            <Typography color="text.secondary" variant="body2">
              IBAN: {transaction.iban ?? "-"} · Payment:{" "}
              {transaction.payment_id
                ? paymentLabelById.get(transaction.payment_id) ?? transaction.payment_id
                : "-"}
            </Typography>
          )}
          renderActions={(transaction) =>
            canManageData ? (
              <TextField
                select
                size="small"
                label="Mit Zahlung matchen"
                value={transaction.payment_id ?? ""}
                onChange={(event) =>
                  void handleMatchBankTransaction(transaction.id, event.target.value)
                }
                sx={{ minWidth: 300 }}
                disabled={bankingActionLoading}
              >
                <MenuItem value="">Keine Auswahl</MenuItem>
                {payments.map((payment) => (
                  <MenuItem key={payment.id} value={payment.id}>
                    {formatCurrency(payment.amount)} · {payment.reference ?? payment.id}
                  </MenuItem>
                ))}
              </TextField>
            ) : null
          }
        />
      ) : null}

      {currentRoute === "documents" ? (
        <Grid container spacing={2}>
          {canManageData ? (
            <Grid item xs={12} md={5}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Dokument hochladen
                  </Typography>
                  <Stack component="form" spacing={2} onSubmit={handleUploadDocument}>
                    <TextField
                      select
                      label="Bezugstyp"
                      value={documentForm.related_model}
                      onChange={(event) =>
                        setDocumentForm({
                          related_model: event.target.value,
                          related_id: "",
                          document_type:
                            event.target.value === "property"
                              ? "property_document"
                              : "invoice_receipt",
                        })
                      }
                    >
                      <MenuItem value="invoice">Invoice</MenuItem>
                      <MenuItem value="property">Property</MenuItem>
                    </TextField>
                    <TextField
                      select
                      label="Bezug"
                      value={documentForm.related_id}
                      onChange={(event) =>
                        setDocumentForm((current) => ({
                          ...current,
                          related_id: event.target.value,
                        }))
                      }
                    >
                      <MenuItem value="">
                        {documentForm.related_model === "property"
                          ? "Immobilie wählen"
                          : "Rechnung wählen"}
                      </MenuItem>
                      {documentTargetOptions.map((option) => (
                        <MenuItem key={option.value} value={option.value}>
                          {option.label}
                        </MenuItem>
                      ))}
                    </TextField>
                    <TextField
                      select
                      label="Dokumenttyp"
                      value={documentForm.document_type}
                      onChange={(event) =>
                        setDocumentForm((current) => ({
                          ...current,
                          document_type: event.target.value,
                        }))
                      }
                    >
                      <MenuItem value="invoice_receipt">Rechnungsbeleg</MenuItem>
                      <MenuItem value="property_document">Objektdokument</MenuItem>
                      <MenuItem value="contract_attachment">Vertragsanhang</MenuItem>
                    </TextField>
                    <Button variant="outlined" component="label">
                      Datei auswählen
                      <input
                        hidden
                        type="file"
                        accept=".pdf,.png,.jpg,.jpeg,.txt"
                        onChange={handleDocumentFileChange}
                      />
                    </Button>
                    <Typography color="text.secondary" variant="body2">
                      {selectedDocumentFile
                        ? `Ausgewählt: ${selectedDocumentFile.name}`
                        : "Unterstützt für den Testlauf: PDF sowie PNG/JPG/JPEG. TXT bleibt nur ein einfacher Fallback für Entwicklung und Debugging."}
                    </Typography>
                    <Typography color="text.secondary" variant="body2">
                      Bestes Ergebnis: PDF mit eingebettetem Text oder gut lesbarer Rechnungs-Scan.
                    </Typography>
                    <Box>
                      <Button
                        type="submit"
                        variant="contained"
                        disabled={documentActionLoading}
                      >
                        Dokument hochladen
                      </Button>
                    </Box>
                  </Stack>
                </CardContent>
              </Card>
            </Grid>
          ) : null}

          <Grid item xs={12} md={canManageData ? 7 : 12}>
            <ManagedListCard
              title="Dokumente"
              items={filteredDocuments}
              emptyText="Keine Dokumente für den aktuellen Filter vorhanden."
              searchValue={documentList.search}
              onSearchChange={(value) =>
                setDocumentList((current) => ({ ...current, search: value, page: 1 }))
              }
              page={documentList.page}
              onPageChange={(page) =>
                setDocumentList((current) => ({
                  ...current,
                  page,
                }))
              }
              pageSize={documentList.pageSize}
              onPageSizeChange={(pageSize) =>
                setDocumentList((current) => ({ ...current, pageSize, page: 1 }))
              }
              searchLabel="Datei, Lieferant oder Rechnungsnummer"
              extraFilters={
                <>
                  <TextField
                    select
                    size="small"
                    label="OCR-Status"
                    value={documentList.ocr_status}
                    onChange={(event) =>
                      setDocumentList((current) => ({
                        ...current,
                        ocr_status: event.target.value,
                        page: 1,
                      }))
                    }
                    sx={{ minWidth: 150 }}
                  >
                    <MenuItem value="all">Alle Stati</MenuItem>
                    <MenuItem value="pending">Pending</MenuItem>
                    <MenuItem value="processed">Processed</MenuItem>
                  </TextField>
                  <TextField
                    select
                    size="small"
                    label="Bezug"
                    value={documentList.related_model}
                    onChange={(event) =>
                      setDocumentList((current) => ({
                        ...current,
                        related_model: event.target.value,
                        page: 1,
                      }))
                    }
                    sx={{ minWidth: 150 }}
                  >
                    <MenuItem value="all">Alle Bezüge</MenuItem>
                    <MenuItem value="invoice">Invoice</MenuItem>
                    <MenuItem value="property">Property</MenuItem>
                  </TextField>
                </>
              }
              renderPrimary={(document) => `${document.file_name} · ${document.document_type}`}
              renderSecondary={(document) =>
                `Status: ${document.ocr_status} · Bezug: ${document.related_model}`
              }
              renderDetails={(document) =>
                document.ocr_result ? (
                  <Typography color="text.secondary" variant="body2">
                    OCR: {String(document.ocr_result.vendor_name ?? "-")} ·{" "}
                    {String(document.ocr_result.invoice_number ?? "-")} ·{" "}
                    {String(document.ocr_result.gross_amount ?? "-")}
                  </Typography>
                ) : (
                  <Typography color="text.secondary" variant="body2">
                    Noch keine OCR-Daten vorhanden.
                  </Typography>
                )
              }
              renderActions={(document) =>
                canManageData ? (
                  <Stack direction="row" spacing={1}>
                    <Button
                      size="small"
                      variant="outlined"
                      onClick={() => void handleProcessDocument(document.id)}
                      disabled={documentActionLoading}
                    >
                      OCR testen
                    </Button>
                    {document.related_model === "invoice" && document.ocr_result ? (
                      <Button
                        size="small"
                        variant="contained"
                        onClick={() => void handleApplyDocumentToInvoice(document.id)}
                        disabled={documentActionLoading}
                      >
                        In Rechnung übernehmen
                      </Button>
                    ) : null}
                  </Stack>
                ) : null
              }
            />
          </Grid>
        </Grid>
      ) : null}
    </Stack>
  );
}
