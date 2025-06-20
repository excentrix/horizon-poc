// frontend/src/hooks/use-chat-stream.ts
"use client";

import { useState, useCallback } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useSession } from "next-auth/react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface StreamMessage {
  type:
    | "token"
    | "facts_update"
    | "task_created"
    | "session_summary"
    | "stream_end"
    | "error";
  data: any;
}

interface Message {
  id: string;
  content: string;
  isUser: boolean;
  timestamp: Date;
}

export function useChatStream() {
  const [isStreaming, setIsStreaming] = useState(false);
  const [currentResponse, setCurrentResponse] = useState("");
  const queryClient = useQueryClient();
  const { data: session } = useSession();

  const sendMessage = useCallback(
    async (
      message: string,
      sessionId: string | null,
      onMessage: (message: Message) => void,
      onTaskCreated: (task: any) => void
    ) => {
      if (!session?.user?.id) {
        throw new Error("Not authenticated - no user ID");
      }

      console.log("🚀 Sending message:", {
        message,
        sessionId,
        userId: session.user.id,
      });

      setIsStreaming(true);
      setCurrentResponse("");

      try {
        // Create request payload
        const requestBody = {
          message: message.trim(),
          session_id: sessionId || null,
        };

        console.log("📤 Request payload:", requestBody);

        // Get session token for authentication
        const response = await fetch(`${API_BASE}/api/chat/stream`, {
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

        console.log("📥 Response status:", response.status);
        console.log(
          "📋 Response headers:",
          Object.fromEntries(response.headers.entries())
        );

        if (!response.ok) {
          const errorText = await response.text();
          console.error("❌ HTTP error response:", errorText);

          if (response.status === 401) {
            throw new Error("Authentication failed. Please sign in again.");
          } else if (response.status === 422) {
            let errorDetail = "Invalid request data";
            try {
              const errorJson = JSON.parse(errorText);
              errorDetail =
                errorJson.detail?.message || errorJson.detail || errorDetail;
            } catch (e) {
              // Use raw error text if JSON parsing fails
              errorDetail = errorText;
            }
            throw new Error(`Validation error: ${errorDetail}`);
          } else {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
          }
        }

        const reader = response.body?.getReader();
        if (!reader) {
          throw new Error("No readable stream");
        }

        const decoder = new TextDecoder();
        let buffer = "";
        let aiResponseContent = "";

        while (true) {
          const { done, value } = await reader.read();

          if (done) {
            console.log("✅ Stream completed");
            break;
          }

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");

          buffer = lines.pop() || "";

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              try {
                const jsonStr = line.slice(6);
                if (jsonStr.trim() === "") continue; // Skip empty data lines

                const streamMessage: StreamMessage = JSON.parse(jsonStr);
                console.log(
                  "📨 Stream message:",
                  streamMessage.type,
                  streamMessage.data
                );

                switch (streamMessage.type) {
                  case "token":
                    aiResponseContent += streamMessage.data;
                    setCurrentResponse(aiResponseContent);
                    break;

                  case "facts_update":
                    queryClient.invalidateQueries({ queryKey: ["facts"] });
                    break;

                  case "task_created":
                    onTaskCreated(streamMessage.data);
                    if (typeof window !== "undefined") {
                      import("canvas-confetti").then((confetti) => {
                        confetti.default({
                          particleCount: 60,
                          spread: 70,
                          origin: { y: 0.9 },
                        });
                      });
                    }
                    break;

                  case "stream_end":
                    console.log("🏁 Stream end received:", streamMessage.data);
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
                    console.error("❌ Stream error:", streamMessage.data);
                    throw new Error(
                      streamMessage.data.message || "Stream error occurred"
                    );
                }
              } catch (parseError) {
                console.error(
                  "❌ Failed to parse stream message:",
                  parseError,
                  "Raw line:",
                  line
                );
              }
            }
          }
        }
      } catch (error) {
        console.error("❌ Chat stream error:", error);
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
