import {
  PropsWithChildren,
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

import { AuthUser, getCurrentUser, login as loginRequest } from "../services/authService";
import { setAuthToken } from "../services/apiClient";
import { DEMO_STORAGE_KEYS, isDemoModeEnabled } from "../demo/demoConfig";

type AuthContextValue = {
  isAuthenticated: boolean;
  isLoadingUser: boolean;
  token: string | null;
  currentUser: AuthUser | null;
  canManageData: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
};

// Der Demo-Modus nutzt einen eigenen Schlüssel, damit Demo- und echte Sitzungen getrennt bleiben.
const STORAGE_KEY = isDemoModeEnabled() ? DEMO_STORAGE_KEYS.session : "propertyhub.auth.token";

const AuthContext = createContext<AuthContextValue>({
  isAuthenticated: false,
  isLoadingUser: false,
  token: null,
  currentUser: null,
  canManageData: false,
  login: async () => {},
  logout: () => {},
});

export function AuthProvider({ children }: PropsWithChildren) {
  const [token, setToken] = useState<string | null>(null);
  const [currentUser, setCurrentUser] = useState<AuthUser | null>(null);
  const [isLoadingUser, setIsLoadingUser] = useState(false);

  async function loadCurrentUserSession() {
    setIsLoadingUser(true);
    try {
      const user = await getCurrentUser();
      setCurrentUser(user);
    } catch {
      window.localStorage.removeItem(STORAGE_KEY);
      setAuthToken(null);
      setToken(null);
      setCurrentUser(null);
    } finally {
      setIsLoadingUser(false);
    }
  }

  useEffect(() => {
    const storedToken = window.localStorage.getItem(STORAGE_KEY);
    if (storedToken) {
      setToken(storedToken);
      setAuthToken(storedToken);
      void loadCurrentUserSession();
    }
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      isAuthenticated: Boolean(token),
      isLoadingUser,
      token,
      currentUser,
      canManageData: currentUser?.role === "owner" || currentUser?.role === "manager",
      login: async (email: string, password: string) => {
        const response = await loginRequest(email, password);
        window.localStorage.setItem(STORAGE_KEY, response.access_token);
        setAuthToken(response.access_token);
        setToken(response.access_token);
        await loadCurrentUserSession();
      },
      logout: () => {
        window.localStorage.removeItem(STORAGE_KEY);
        setAuthToken(null);
        setToken(null);
        setCurrentUser(null);
      },
    }),
    [currentUser, isLoadingUser, token],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}
