import { PropsWithChildren } from "react";
import ApartmentIcon from "@mui/icons-material/Apartment";
import {
  AppBar,
  Box,
  Button,
  Container,
  Stack,
  Toolbar,
  Typography,
} from "@mui/material";

import { useAuth } from "../context/AuthContext";

export function AppShell({ children }: PropsWithChildren) {
  const { isAuthenticated, logout } = useAuth();

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
              <Button color="inherit" onClick={logout}>
                Logout
              </Button>
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
