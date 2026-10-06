import { FormEvent, useEffect, useMemo, useState } from "react";
import { Alert, Box, Button, Card, CardContent, Stack, TextField, Typography } from "@mui/material";

import { DEMO_PASSWORD, isDemoModeEnabled } from "../demo/demoConfig";
import { getInvitationInfo, setupPassword } from "../services/authService";

export function SetupPasswordPage() {
  const searchParams = useMemo(() => new URLSearchParams(window.location.search), []);
  const token = searchParams.get("token") ?? "";

  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [info, setInfo] = useState<{
    email: string;
    full_name?: string | null;
    organization_name: string;
    role: string;
  } | null>(null);
  const [loading, setLoading] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!token) {
      setErrorMessage("Einladungstoken fehlt.");
      return;
    }

    setLoading(true);
    void getInvitationInfo(token)
      .then((response) => {
        setInfo(response);
        setFullName(response.full_name ?? "");
      })
      .catch(() => {
        setErrorMessage("Einladung konnte nicht geladen werden.");
      })
      .finally(() => {
        setLoading(false);
      });
  }, [token]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrorMessage(null);
    setSuccessMessage(null);
    setLoading(true);
    try {
      await setupPassword(token, password, fullName || null);
      setSuccessMessage("Passwort wurde gesetzt. Du kannst dich jetzt anmelden.");
      setPassword("");
      window.history.pushState({}, "", import.meta.env.BASE_URL);
    } catch {
      setErrorMessage("Passwort konnte nicht gesetzt werden.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Stack spacing={3}>
      <div>
        <Typography variant="h4" gutterBottom>
          Passwort festlegen
        </Typography>
        <Typography color="text.secondary">
          Einladung annehmen und den Zugang für PropertyHub aktivieren.
        </Typography>
      </div>

      {isDemoModeEnabled() ? (
        <Alert severity="warning">
          Demo-Modus: Die Einladung wird nur simuliert. Das gewählte Passwort wird nicht gespeichert –
          die Anmeldung erfolgt anschließend mit dem Demo-Passwort <strong>{DEMO_PASSWORD}</strong>.
        </Alert>
      ) : null}
      {loading ? <Alert severity="info">Einladung wird geladen...</Alert> : null}
      {errorMessage ? <Alert severity="error">{errorMessage}</Alert> : null}
      {successMessage ? <Alert severity="success">{successMessage}</Alert> : null}

      <Card>
        <CardContent>
          <Stack spacing={2} component="form" onSubmit={handleSubmit}>
            <Typography>
              <strong>Organisation:</strong> {info?.organization_name ?? "-"}
            </Typography>
            <Typography>
              <strong>E-Mail:</strong> {info?.email ?? "-"}
            </Typography>
            <Typography>
              <strong>Rolle:</strong> {info?.role ?? "-"}
            </Typography>
            <TextField
              label="Name"
              value={fullName}
              onChange={(event) => setFullName(event.target.value)}
            />
            <TextField
              label="Neues Passwort"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
            <Box>
              <Button type="submit" variant="contained" disabled={!token || loading || !password}>
                Passwort speichern
              </Button>
            </Box>
          </Stack>
        </CardContent>
      </Card>
    </Stack>
  );
}
