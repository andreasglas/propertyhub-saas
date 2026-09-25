import {
  PropsWithChildren,
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

import { login as loginRequest } from "../services/authService";
import { setAuthToken } from "../services/apiClient";

type AuthContextValue = {
  isAuthenticated: boolean;
  token: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
};

const STORAGE_KEY = "propertyhub.auth.token";

const AuthContext = createContext<AuthContextValue>({
  isAuthenticated: false,
  token: null,
  login: async () => {},
  logout: () => {},
});

export function AuthProvider({ children }: PropsWithChildren) {
  const [token, setToken] = useState<string | null>(null);

  useEffect(() => {
    const storedToken = window.localStorage.getItem(STORAGE_KEY);
    if (storedToken) {
      setToken(storedToken);
      setAuthToken(storedToken);
    }
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      isAuthenticated: Boolean(token),
      token,
      login: async (email: string, password: string) => {
        const response = await loginRequest(email, password);
        window.localStorage.setItem(STORAGE_KEY, response.access_token);
        setAuthToken(response.access_token);
        setToken(response.access_token);
      },
      logout: () => {
        window.localStorage.removeItem(STORAGE_KEY);
        setAuthToken(null);
        setToken(null);
      },
    }),
    [token],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}
