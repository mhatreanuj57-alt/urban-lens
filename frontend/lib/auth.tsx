"use client";

import {
  createContext, useCallback, useContext, useEffect, useMemo, useState,
} from "react";
import { authApi, getToken, setToken, type User } from "@/lib/api";
import { supabase } from "@/lib/supabase";

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

async function loadMe(): Promise<User> {
  const me = await authApi.me();
  return me;
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    async function restore() {
      // Prefer a fresh Supabase session (handles token refresh); fall back to a
      // stored legacy token so pre-Supabase sessions keep working.
      const { data } = await supabase.auth.getSession();
      if (data.session?.access_token) {
        setToken(data.session.access_token);
      } else if (!getToken()) {
        setLoading(false);
        return;
      }
      try {
        const me = await loadMe();
        if (!cancelled) setUser(me);
      } catch {
        setToken(null);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    restore();
    const { data: sub } = supabase.auth.onAuthStateChange((_event, session) => {
      if (session?.access_token) setToken(session.access_token);
    });
    return () => {
      cancelled = true;
      sub.subscription.unsubscribe();
    };
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });
    if (error || !data.session) {
      throw new Error(error?.message || "Invalid email or password");
    }
    setToken(data.session.access_token);
    const me = await loadMe();
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
      const { data: signed, error } = await supabase.auth.signUp({
        email: data.email,
        password: data.password,
        options: { data: { display_name: data.display_name } },
      });
      if (error) throw new Error(error.message);
      // Email confirmation is off in dev → a session comes back immediately.
      if (signed.session?.access_token) {
        setToken(signed.session.access_token);
        const me = await loadMe();
        setUser(me);
        return me;
      }
      if (signed.user && !signed.session) {
        throw new Error(
          "Check your inbox — confirm your email address, then sign in.",
        );
      }
      return login(data.email, data.password);
    },
    [login],
  );

  const logout = useCallback(() => {
    void supabase.auth.signOut();
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
