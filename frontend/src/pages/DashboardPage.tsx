import { Alert, Card, CardContent, Grid, Stack, Typography } from "@mui/material";

const kpis = [
  { label: "Mieteinnahmen", value: "0 €" },
  { label: "Offene Forderungen", value: "0 €" },
  { label: "Leerstand", value: "0 %" },
  { label: "Offene Rechnungen", value: "0" },
];

export function DashboardPage() {
  return (
    <Stack spacing={3}>
      <div>
        <Typography variant="h4" gutterBottom>
          Immobilienverwaltung Dashboard
        </Typography>
        <Typography color="text.secondary">
          Initiales SaaS-Frontend mit Material UI, API-Client und modularer Struktur.
        </Typography>
      </div>

      <Alert severity="info">
        Das Grundgerüst ist bereit für Authentifizierung, Mandantenkontext und fachliche Workflows.
      </Alert>

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
    </Stack>
  );
}
