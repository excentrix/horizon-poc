// frontend/src/hooks/use-chat.ts
"use client";

import { useState } from "react";
import axios from "axios";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function useChat() {
  const [isLoading, setIsLoading] = useState(false);

  const sendMessage = async (
    message: string,
    sessionId: string | null = null
  ) => {
    setIsLoading(true);
    try {
      const response = await axios.post(`${API_BASE}/api/chat`, {
        message,
        session_id: sessionId,
      });

      // For now, return a mock response since streaming isn't implemented yet
      return {
        content: `Thanks for your message: "${message}". I'm here to help you learn and grow!`,
        facts: {},
        task: null,
      };
    } catch (error) {
      console.error("Chat API error:", error);
      throw new Error("Failed to send message");
    } finally {
      setIsLoading(false);
    }
  };

  return { sendMessage, isLoading };
}
