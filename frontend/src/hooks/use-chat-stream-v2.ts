// frontend/src/hooks/use-chat-stream-v2.ts
"use client";

import { useState, useCallback } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useSession } from "next-auth/react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface StreamMessage {
  type: "token" | "stream_complete" | "stream_end" | "error";
  data: any;
}

interface Message {
  id: string;
  content: string;
  isUser: boolean;
  timestamp: Date;
}

export function useChatStreamV2() {
  const [isStreaming, setIsStreaming] = useState(false);
  const [currentResponse, setCurrentResponse] = useState("");
  const queryClient = useQueryClient();
  const { data: session } = useSession();

  const sendMessage = useCallback(
    async (
      message: string,
      sessionId: string | null,
      onMessage: (message: Message) => void
    ) => {
      if (!session?.user?.id) {
        throw new Error("Not authenticated");
      }

      console.log("🚀 Sending message to v2 API:", { message, sessionId });

      setIsStreaming(true);
      setCurrentResponse("");

      try {
        const requestBody = {
          message: message.trim(),
          session_id: sessionId || null,
        };

        // Call v2 API
        const response = await fetch(`${API_BASE}/api/v2/chat/stream`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${btoa(
              JSON.stringify({
                email: session.user.email,
                id: session.user.id,
                name: session.user.name,
              })
            )}`,
          },
          body: JSON.stringify(requestBody),
        });

        console.log("📥 v2 API Response status:", response.status);

        if (!response.ok) {
          const errorText = await response.text();
          console.error("❌ v2 API error:", errorText);
          throw new Error(`v2 API Error: ${response.status}`);
        }

        const reader = response.body?.getReader();
        if (!reader) throw new Error("No readable stream");

        const decoder = new TextDecoder();
        let buffer = "";
        let aiResponseContent = "";

        while (true) {
          const { done, value } = await reader.read();

          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              try {
                const jsonStr = line.slice(6);
                if (jsonStr.trim() === "") continue;

                const streamMessage: StreamMessage = JSON.parse(jsonStr);
                console.log(
                  "📨 v2 Stream message:",
                  streamMessage.type,
                  streamMessage.data
                );

                switch (streamMessage.type) {
                  case "token":
                    aiResponseContent += streamMessage.data;
                    setCurrentResponse(aiResponseContent);
                    break;

                  case "stream_complete":
                  case "stream_end":
                    console.log("🏁 v2 Stream end:", streamMessage.data);
                    if (aiResponseContent) {
                      onMessage({
                        id: Date.now().toString(),
                        content: aiResponseContent,
                        isUser: false,
                        timestamp: new Date(),
                      });
                    }
                    setCurrentResponse("");
                    return;

                  case "error":
                    console.error("❌ v2 Stream error:", streamMessage.data);
                    throw new Error(
                      streamMessage.data.message || "Stream error"
                    );
                }
              } catch (parseError) {
                console.error(
                  "❌ Failed to parse v2 stream message:",
                  parseError
                );
              }
            }
          }
        }
      } catch (error) {
        console.error("❌ v2 Chat stream error:", error);
        throw error;
      } finally {
        setIsStreaming(false);
        setCurrentResponse("");
      }
    },
    [queryClient, session]
  );

  return {
    sendMessage,
    isStreaming,
    currentResponse,
  };
}
