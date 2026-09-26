import { PropsWithChildren } from "react";
import ApartmentIcon from "@mui/icons-material/Apartment";
import {
  AppBar,
  Box,
  Button,
  Chip,
  Container,
  Stack,
  Toolbar,
  Typography,
} from "@mui/material";

import { AppRoute } from "../appRoutes";
import { useAuth } from "../context/AuthContext";

const navigationItems: Array<{ route: AppRoute; label: string }> = [
  { route: "overview", label: "Übersicht" },
  { route: "properties", label: "Immobilien" },
  { route: "units", label: "Einheiten" },
  { route: "tenants", label: "Mieter" },
  { route: "contracts", label: "Verträge" },
  { route: "accounting", label: "Accounting" },
  { route: "billing", label: "Billing" },
  { route: "banking", label: "Banking" },
  { route: "documents", label: "Dokumente" },
];

type AppShellProps = PropsWithChildren<{
  currentRoute: AppRoute;
  onNavigate: (route: AppRoute) => void;
}>;

export function AppShell({ children, currentRoute, onNavigate }: AppShellProps) {
  const { currentUser, isAuthenticated, logout } = useAuth();

  return (
    <Box sx={{ bgcolor: "background.default", minHeight: "100vh" }}>
      <AppBar position="static" elevation={0}>
        <Toolbar>
          <Stack
            direction="row"
            spacing={1.5}
            alignItems="center"
            justifyContent="space-between"
            sx={{ width: "100%" }}
          >
            <Stack direction="row" spacing={1.5} alignItems="center">
              <ApartmentIcon />
              <Typography variant="h6" component="div">
                PropertyHub
              </Typography>
            </Stack>

            {isAuthenticated ? (
              <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap">
                {navigationItems.map((item) => (
                  <Button
                    key={item.route}
                    color="inherit"
                    variant={currentRoute === item.route ? "outlined" : "text"}
                    onClick={() => onNavigate(item.route)}
                    sx={{
                      borderColor:
                        currentRoute === item.route ? "rgba(255,255,255,0.4)" : undefined,
                    }}
                  >
                    {item.label}
                  </Button>
                ))}
                {currentUser ? (
                  <Chip
                    label={`Rolle: ${currentUser.role}`}
                    color="default"
                    size="small"
                    sx={{ bgcolor: "rgba(255,255,255,0.16)", color: "white" }}
                  />
                ) : null}
                <Button color="inherit" onClick={logout}>
                  Logout
                </Button>
              </Stack>
            ) : null}
          </Stack>
        </Toolbar>
      </AppBar>
      <Container maxWidth="lg" sx={{ py: 4 }}>
        {children}
      </Container>
    </Box>
  );
}
