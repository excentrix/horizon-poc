// frontend/src/hooks/use-chat-stream.ts
"use client";

import { useState, useCallback } from "react";
import { useQueryClient } from "@tanstack/react-query";

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

  const sendMessage = useCallback(
    async (
      message: string,
      sessionId: string | null,
      userEmail: string,
      onMessage: (message: Message) => void,
      onTaskCreated: (task: any) => void
    ) => {
      setIsStreaming(true);
      setCurrentResponse("");

      try {
        const response = await fetch(`${API_BASE}/api/chat/stream`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            message,
            session_id: sessionId,
            user_email: userEmail,
          }),
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
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

          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");

          // Keep the last incomplete line in buffer
          buffer = lines.pop() || "";

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              try {
                const jsonStr = line.slice(6); // Remove 'data: '
                const streamMessage: StreamMessage = JSON.parse(jsonStr);

                switch (streamMessage.type) {
                  case "token":
                    aiResponseContent += streamMessage.data;
                    setCurrentResponse(aiResponseContent);
                    break;

                  case "facts_update":
                    // Invalidate facts query to refetch
                    queryClient.invalidateQueries({ queryKey: ["facts"] });
                    break;

                  case "task_created":
                    onTaskCreated(streamMessage.data);
                    // Show confetti animation
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
                    // Add final AI message
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
                    throw new Error(streamMessage.data.message);
                }
              } catch (parseError) {
                console.error("Failed to parse stream message:", parseError);
              }
            }
          }
        }
      } catch (error) {
        console.error("Chat stream error:", error);
        throw error;
      } finally {
        setIsStreaming(false);
        setCurrentResponse("");
      }
    },
    [queryClient]
  );

  return {
    sendMessage,
    isStreaming,
    currentResponse,
  };
}
