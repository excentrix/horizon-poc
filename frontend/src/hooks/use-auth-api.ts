// frontend/src/hooks/use-auth-api.ts
"use client";

import { useSession } from "next-auth/react";
import axios from "axios";
import { useCallback } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function useAuthenticatedAPI() {
  const { data: session } = useSession();

  const createAuthenticatedAxios = useCallback(() => {
    const instance = axios.create({
      baseURL: API_BASE,
    });

    // Add auth interceptor
    instance.interceptors.request.use(
      (config) => {
        if (session?.user?.email) {
          // For now, we'll create a simple token
          // In production, use the actual NextAuth JWT
          const token = btoa(JSON.stringify({ email: session.user.email }));
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    return instance;
  }, [session]);

  return {
    authenticatedAxios: createAuthenticatedAxios(),
    isAuthenticated: !!session?.user?.email,
  };
}
