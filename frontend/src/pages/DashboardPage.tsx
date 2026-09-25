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
import { Property, listProperties } from "../services/propertyService";

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
  const [loadError, setLoadError] = useState<string | null>(null);
  const [entryForm, setEntryForm] = useState({
    property_id: "",
    entry_type: "expense",
    category: "insurance",
    amount: "0",
    booking_date: "",
  });

  async function loadDashboardData() {
    setLoading(true);
    setLoadError(null);
    try {
      const [loadedProperties, loadedEntries] = await Promise.all([
        listProperties(),
        listAccountingEntries(),
      ]);
      setProperties(loadedProperties);
      setEntries(loadedEntries);
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
    { label: "Immobilien", value: String(properties.length) },
    { label: "Buchungssätze", value: String(entries.length) },
    { label: "Gesamtbetrag", value: `${totalAccountingAmount.toFixed(2)} €` },
    { label: "Letzte Kategorie", value: entries[0]?.category ?? "-" },
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
    </Stack>
  );
}
