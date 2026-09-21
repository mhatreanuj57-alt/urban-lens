"use client";

import {
  createContext, useCallback, useContext, useEffect, useMemo, useState,
} from "react";
import { authApi, getToken, setToken, type User } from "@/lib/api";

interface AuthState {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<User>;
  register: (data: {
    email: string;
    password: string;
    display_name?: string;
    consent_training?: boolean;
  }) => Promise<User>;
  logout: () => void;
  isModerator: boolean;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    async function restore() {
      if (!getToken()) {
        setLoading(false);
        return;
      }
      try {
        const me = await authApi.me();
        if (!cancelled) setUser(me);
      } catch {
        setToken(null);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    restore();
    return () => {
      cancelled = true;
    };
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const token = await authApi.login(email, password);
    setToken(token.access_token);
    const me = await authApi.me();
    setUser(me);
    return me;
  }, []);

  const register = useCallback(
    async (data: {
      email: string;
      password: string;
      display_name?: string;
      consent_training?: boolean;
    }) => {
      await authApi.register(data);
      return login(data.email, data.password);
    },
    [login],
  );

  const logout = useCallback(() => {
    setToken(null);
    setUser(null);
  }, []);

  const value = useMemo<AuthState>(
    () => ({
      user,
      loading,
      login,
      register,
      logout,
      isModerator: user?.role === "moderator" || user?.role === "admin",
    }),
    [user, loading, login, register, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
