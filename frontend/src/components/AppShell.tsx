import { PropsWithChildren, useMemo, useState } from "react";
import ApartmentIcon from "@mui/icons-material/Apartment";
import AssignmentIcon from "@mui/icons-material/Assignment";
import BusinessIcon from "@mui/icons-material/Business";
import DescriptionIcon from "@mui/icons-material/Description";
import GroupsIcon from "@mui/icons-material/Groups";
import HistoryIcon from "@mui/icons-material/History";
import HomeWorkIcon from "@mui/icons-material/HomeWork";
import MenuIcon from "@mui/icons-material/Menu";
import PlumbingIcon from "@mui/icons-material/Plumbing";
import PaidIcon from "@mui/icons-material/Paid";
import ReceiptLongIcon from "@mui/icons-material/ReceiptLong";
import TableChartIcon from "@mui/icons-material/TableChart";
import VillaIcon from "@mui/icons-material/Villa";
import {
  AppBar,
  Box,
  Button,
  Chip,
  Container,
  Divider,
  Drawer,
  IconButton,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Stack,
  Toolbar,
  Typography,
} from "@mui/material";

import { AppRoute } from "../appRoutes";
import { useAuth } from "../context/AuthContext";

const navigationItems: Array<{ route: AppRoute; label: string; icon: JSX.Element }> = [
  { route: "overview", label: "Übersicht", icon: <ApartmentIcon fontSize="small" /> },
  { route: "activity", label: "Aktivität", icon: <HistoryIcon fontSize="small" /> },
  {
    route: "organization",
    label: "Organisation",
    icon: <BusinessIcon fontSize="small" />,
  },
  { route: "users", label: "Benutzer", icon: <GroupsIcon fontSize="small" /> },
  { route: "properties", label: "Immobilien", icon: <VillaIcon fontSize="small" /> },
  { route: "units", label: "Einheiten", icon: <HomeWorkIcon fontSize="small" /> },
  { route: "tenants", label: "Mieter", icon: <GroupsIcon fontSize="small" /> },
  { route: "contracts", label: "Verträge", icon: <AssignmentIcon fontSize="small" /> },
  { route: "operating-costs", label: "Nebenkosten", icon: <PlumbingIcon fontSize="small" /> },
  { route: "accounting", label: "Accounting", icon: <TableChartIcon fontSize="small" /> },
  { route: "billing", label: "Billing", icon: <ReceiptLongIcon fontSize="small" /> },
  { route: "banking", label: "Banking", icon: <PaidIcon fontSize="small" /> },
  { route: "documents", label: "Dokumente", icon: <DescriptionIcon fontSize="small" /> },
];

type AppShellProps = PropsWithChildren<{
  currentRoute: AppRoute;
  onNavigate: (route: AppRoute) => void;
}>;

export function AppShell({ children, currentRoute, onNavigate }: AppShellProps) {
  const { currentUser, isAuthenticated, logout } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);
  const isSetupRoute = currentRoute === "setup-password";

  const currentItem = useMemo(
    () => navigationItems.find((item) => item.route === currentRoute),
    [currentRoute],
  );

  const navigationContent = (
    <List sx={{ minWidth: 260 }}>
      {navigationItems.map((item) => (
        <ListItemButton
          key={item.route}
          selected={currentRoute === item.route}
          onClick={() => {
            onNavigate(item.route);
            setMobileOpen(false);
          }}
          sx={{ borderRadius: 2, mx: 1, my: 0.5 }}
        >
          <ListItemIcon sx={{ minWidth: 40 }}>{item.icon}</ListItemIcon>
          <ListItemText primary={item.label} />
        </ListItemButton>
      ))}
    </List>
  );

  return (
    <Box sx={{ bgcolor: "background.default", minHeight: "100vh" }}>
      <AppBar position="static" elevation={0}>
        <Toolbar sx={{ py: 1 }}>
          <Stack
            direction={{ xs: "column", md: "row" }}
            spacing={2}
            alignItems={{ xs: "stretch", md: "center" }}
            justifyContent="space-between"
            sx={{ width: "100%" }}
          >
            <Stack direction="row" spacing={1.5} alignItems="center" justifyContent="space-between">
              <Stack direction="row" spacing={1.5} alignItems="center">
                <ApartmentIcon />
                <Box>
                  <Typography variant="h6" component="div">
                    PropertyHub
                  </Typography>
                  {isAuthenticated && currentItem && !isSetupRoute ? (
                    <Typography variant="body2" sx={{ opacity: 0.85 }}>
                      {currentItem.label}
                    </Typography>
                  ) : null}
                </Box>
              </Stack>

              {isAuthenticated && !isSetupRoute ? (
                <IconButton
                  color="inherit"
                  sx={{ display: { xs: "inline-flex", md: "none" } }}
                  onClick={() => setMobileOpen(true)}
                >
                  <MenuIcon />
                </IconButton>
              ) : null}
            </Stack>

            {isAuthenticated && !isSetupRoute ? (
              <Stack spacing={1.5} sx={{ width: { xs: "100%", md: "auto" } }}>
                <Stack
                  direction="row"
                  spacing={1}
                  alignItems="center"
                  flexWrap="wrap"
                  sx={{ display: { xs: "none", md: "flex" } }}
                >
                  {navigationItems.map((item) => (
                    <Button
                      key={item.route}
                      color="inherit"
                      variant={currentRoute === item.route ? "contained" : "text"}
                      startIcon={item.icon}
                      onClick={() => onNavigate(item.route)}
                      sx={{
                        bgcolor:
                          currentRoute === item.route ? "rgba(255,255,255,0.18)" : "transparent",
                        "&:hover": {
                          bgcolor: "rgba(255,255,255,0.14)",
                        },
                      }}
                    >
                      {item.label}
                    </Button>
                  ))}
                </Stack>

                <Stack direction="row" spacing={1} alignItems="center" justifyContent="flex-end">
                  {currentUser ? (
                    <>
                      <Chip
                        label={currentUser.organization_id.slice(0, 8)}
                        color="default"
                        size="small"
                        sx={{ bgcolor: "rgba(255,255,255,0.16)", color: "white" }}
                      />
                      <Chip
                        label={`${currentUser.full_name ?? currentUser.email} · ${currentUser.role}`}
                        color="default"
                        size="small"
                        sx={{ bgcolor: "rgba(255,255,255,0.16)", color: "white" }}
                      />
                    </>
                  ) : null}
                  <Button color="inherit" onClick={logout}>
                    Logout
                  </Button>
                </Stack>
              </Stack>
            ) : null}
          </Stack>
        </Toolbar>
      </AppBar>

      {isAuthenticated && !isSetupRoute ? (
        <Drawer anchor="left" open={mobileOpen} onClose={() => setMobileOpen(false)}>
          <Box sx={{ width: 280, py: 2 }}>
            <Stack spacing={1} sx={{ px: 2, pb: 2 }}>
              <Typography variant="h6">PropertyHub</Typography>
              {currentUser ? (
                <Typography color="text.secondary" variant="body2">
                  {currentUser.full_name ?? currentUser.email}
                </Typography>
              ) : null}
            </Stack>
            <Divider />
            {navigationContent}
            <Divider sx={{ my: 1 }} />
            <Box sx={{ px: 2 }}>
              <Button fullWidth variant="outlined" onClick={logout}>
                Logout
              </Button>
            </Box>
          </Box>
        </Drawer>
      ) : null}

      <Container maxWidth="xl" sx={{ py: { xs: 3, md: 4 } }}>
        {children}
      </Container>
    </Box>
  );
}
