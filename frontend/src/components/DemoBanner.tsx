import { useState } from "react";
import { Alert, AlertTitle, Box, Button, Collapse, Stack, Typography } from "@mui/material";

import { resetDemoData } from "../demo/demoConfig";

const demoLimitations = [
  "Alle Daten sind fiktiv und werden ausschließlich lokal in diesem Browser gespeichert.",
  "Es werden keine Server-, Bank-, E-Mail- oder OCR-Dienste kontaktiert.",
  "Einladungen werden nicht per E-Mail versendet; der Einladungslink funktioniert nur in diesem Browser.",
  "Hochgeladene Dateien verlassen das Gerät nicht – gespeichert werden nur Dateiname und Metadaten.",
  "OCR und Bankimport sind Simulationen; Passwortänderungen werden nicht gespeichert.",
];

export function DemoBanner() {
  const [showDetails, setShowDetails] = useState(false);

  function handleReset() {
    if (!window.confirm("Alle Demo-Änderungen verwerfen und Beispieldaten neu laden?")) {
      return;
    }
    resetDemoData();
    window.location.reload();
  }

  return (
    <Alert
      severity="warning"
      variant="outlined"
      sx={{ mb: 3, bgcolor: "background.paper" }}
      data-testid="demo-banner"
    >
      <AlertTitle>Demo-Modus</AlertTitle>
      <Typography variant="body2">
        Ausschließlich fiktive Beispieldaten – Änderungen haben keine Produktivwirkung.
      </Typography>
      <Stack direction="row" flexWrap="wrap" sx={{ mt: 1, gap: 1 }}>
        <Button size="small" variant="outlined" color="warning" onClick={handleReset}>
          Demo-Daten zurücksetzen
        </Button>
        <Button size="small" color="warning" onClick={() => setShowDetails((current) => !current)}>
          {showDetails ? "Hinweise ausblenden" : "Hinweise & Grenzen"}
        </Button>
      </Stack>
      <Collapse in={showDetails}>
        <Box component="ul" sx={{ pl: 2.5, mb: 0, mt: 1 }}>
          {demoLimitations.map((item) => (
            <Typography key={item} component="li" variant="body2">
              {item}
            </Typography>
          ))}
        </Box>
      </Collapse>
    </Alert>
  );
}
