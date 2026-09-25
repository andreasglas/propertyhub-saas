import { FormEvent, useEffect, useMemo, useState } from "react";
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
  Stack,
  TextField,
  Typography,
} from "@mui/material";

import { useAuth } from "../context/AuthContext";
import {
  AccountingEntry,
  createAccountingEntry,
  listAccountingEntries,
} from "../services/accountingService";
import { createInvoice, Invoice, listInvoices } from "../services/invoiceService";
import { createPayment, listPayments, Payment } from "../services/paymentService";
import { Property, listProperties } from "../services/propertyService";
import { DashboardReport, getDashboardReport } from "../services/reportService";

const defaultCredentials = {
  email: "admin@example.com",
  password: "test-password",
};

export function DashboardPage() {
  const { isAuthenticated, login } = useAuth();
  const [email, setEmail] = useState(defaultCredentials.email);
  const [password, setPassword] = useState(defaultCredentials.password);
  const [loginError, setLoginError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [properties, setProperties] = useState<Property[]>([]);
  const [entries, setEntries] = useState<AccountingEntry[]>([]);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [payments, setPayments] = useState<Payment[]>([]);
  const [report, setReport] = useState<DashboardReport | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
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

  async function loadDashboardData() {
    setLoading(true);
    setLoadError(null);
    try {
      const [
        loadedProperties,
        loadedEntries,
        loadedInvoices,
        loadedPayments,
        loadedReport,
      ] = await Promise.all([
        listProperties(),
        listAccountingEntries(),
        listInvoices(),
        listPayments(),
        getDashboardReport(),
      ]);
      setProperties(loadedProperties);
      setEntries(loadedEntries);
      setInvoices(loadedInvoices);
      setPayments(loadedPayments);
      setReport(loadedReport);
    } catch {
      setLoadError("Daten konnten nicht geladen werden.");
    } finally {
      setLoading(false);
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

  async function handleLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoginError(null);
    try {
      await login(email, password);
    } catch {
      setLoginError("Login fehlgeschlagen. Bitte Zugangsdaten prüfen.");
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

  if (!isAuthenticated) {
    return (
      <Stack spacing={3}>
        <div>
          <Typography variant="h4" gutterBottom>
            PropertyHub Dashboard
          </Typography>
          <Typography color="text.secondary">
            Erster Frontend-Slice mit Login und Buchungsübersicht.
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

  const kpis = [
    { label: "Immobilien", value: String(report?.properties_count ?? properties.length) },
    { label: "Rechnungen offen", value: String(report?.open_invoices_count ?? 0) },
    { label: "Zahlungen", value: String(report?.payments_count ?? payments.length) },
    {
      label: "Accounting Gesamt",
      value: `${(report?.total_expense_amount ?? totalAccountingAmount).toFixed(2)} €`,
    },
  ];

  return (
    <Stack spacing={3}>
      <div>
        <Typography variant="h4" gutterBottom>
          Immobilienverwaltung Dashboard
        </Typography>
        <Typography color="text.secondary">
          Erste integrierte Oberfläche für Login, Immobilien und Accounting Entries.
        </Typography>
      </div>

      {loadError ? <Alert severity="error">{loadError}</Alert> : null}
      {loading ? <Alert severity="info">Daten werden geladen...</Alert> : null}

      <Grid container spacing={2}>
        {kpis.map((kpi) => (
          <Grid key={kpi.label} item xs={12} sm={6} md={3}>
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
                Immobilien
              </Typography>
              <List dense>
                {properties.map((property) => (
                  <ListItem key={property.id} disableGutters>
                    <ListItemText
                      primary={property.name}
                      secondary={`${property.city ?? "-"} · ${property.property_type}`}
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
                  {properties.map((property) => (
                    <MenuItem key={property.id} value={property.id}>
                      {property.name}
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
      </Grid>

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
                  {properties.map((property) => (
                    <MenuItem key={property.id} value={property.id}>
                      {property.name}
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
                  {invoices.map((invoice) => (
                    <MenuItem key={invoice.id} value={invoice.id}>
                      {invoice.vendor_name} · {invoice.gross_amount.toFixed(2)} €
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

      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Letzte Buchungssätze
          </Typography>
          <List dense>
            {entries.map((entry) => (
              <ListItem key={entry.id} disableGutters>
                <ListItemText
                  primary={`${entry.entry_type} · ${entry.amount.toFixed(2)} €`}
                  secondary={`${entry.category ?? "-"} · ${entry.booking_date ?? "-"}`}
                />
              </ListItem>
            ))}
            {!entries.length ? (
              <Typography color="text.secondary">
                Noch keine Accounting Entries vorhanden.
              </Typography>
            ) : null}
          </List>
        </CardContent>
      </Card>

      <Grid container spacing={2}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Letzte Rechnungen
              </Typography>
              <List dense>
                {invoices.map((invoice) => (
                  <ListItem key={invoice.id} disableGutters>
                    <ListItemText
                      primary={`${invoice.vendor_name} · ${invoice.gross_amount.toFixed(2)} €`}
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
                Letzte Zahlungen
              </Typography>
              <List dense>
                {payments.map((payment) => (
                  <ListItem key={payment.id} disableGutters>
                    <ListItemText
                      primary={`${payment.amount.toFixed(2)} €`}
                      secondary={`${payment.reference ?? "-"} · ${payment.booking_date ?? "-"}`}
                    />
                  </ListItem>
                ))}
                {!payments.length ? (
                  <Typography color="text.secondary">
                    Noch keine Zahlungen vorhanden.
                  </Typography>
                ) : null}
              </List>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Stack>
  );
}
