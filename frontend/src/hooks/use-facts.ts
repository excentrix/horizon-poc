// frontend/src/hooks/use-facts.ts
"use client";

import { useQuery } from "@tanstack/react-query";
import { useAuthenticatedAPI } from "./use-auth-api";

export function useFacts() {
  const { authenticatedAxios, isAuthenticated } = useAuthenticatedAPI();

  return useQuery({
    queryKey: ["facts"],
    queryFn: async () => {
      try {
        const response = await authenticatedAxios.get("/api/facts");
        return response.data;
      } catch (error) {
        console.error("Facts API error:", error);
        return {
          profile: {},
          tasks: [],
          sessions: [],
        };
      }
    },
    enabled: isAuthenticated, // Only run if user is authenticated
    staleTime: 5 * 1000,
    refetchInterval: 30 * 1000,
    retry: 3,
  });
}
