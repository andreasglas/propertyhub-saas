import { PropsWithChildren } from "react";
import ApartmentIcon from "@mui/icons-material/Apartment";
import {
  AppBar,
  Box,
  Container,
  Stack,
  Toolbar,
  Typography,
} from "@mui/material";

export function AppShell({ children }: PropsWithChildren) {
  return (
    <Box sx={{ bgcolor: "background.default", minHeight: "100vh" }}>
      <AppBar position="static" elevation={0}>
        <Toolbar>
          <Stack direction="row" spacing={1.5} alignItems="center">
            <ApartmentIcon />
            <Typography variant="h6" component="div">
              PropertyHub
            </Typography>
          </Stack>
        </Toolbar>
      </AppBar>
      <Container maxWidth="lg" sx={{ py: 4 }}>
        {children}
      </Container>
    </Box>
  );
}
