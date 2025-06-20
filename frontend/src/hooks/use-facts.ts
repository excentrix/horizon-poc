// frontend/src/hooks/use-facts.ts
"use client";

import { useQuery } from "@tanstack/react-query";
import axios from "axios";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function useFacts(userEmail: string = "demo@horizon.ai") {
  return useQuery({
    queryKey: ["facts", userEmail],
    queryFn: async () => {
      try {
        const response = await axios.get(`${API_BASE}/api/facts`, {
          params: {
            user_email: userEmail,
          },
        });
        return response.data;
      } catch (error) {
        console.error("Facts API error:", error);
        // Return empty data structure on error
        return {
          profile: {},
          tasks: [],
          sessions: [],
        };
      }
    },
    staleTime: 5 * 1000, // 5 seconds
    refetchInterval: 30 * 1000, // Auto-refresh every 30s
    retry: 3,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  });
}
