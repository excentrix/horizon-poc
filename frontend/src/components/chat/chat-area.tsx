// frontend/src/components/chat/chat-area.tsx (add test button temporarily)
"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { ChatBubble } from "./chat-bubble";
import { ChatInput } from "./chat-input";
import { TypingIndicator } from "./typing-indicator";
import { useChatStream } from "@/hooks/use-chat-stream";
import { AlertTriangle, LogOut, TestTube } from "lucide-react";
import { signOut, useSession } from "next-auth/react";

interface Message {
  id: string;
  content: string;
  isUser: boolean;
  timestamp: Date;
}

interface ChatAreaProps {
  sessionId: string | null;
  onSessionChange: (sessionId: string) => void;
}

export function ChatArea({ sessionId, onSessionChange }: ChatAreaProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      content:
        "Hello! I'm Horizon, your AI learning mentor. I'm here to help you with your academic journey, career planning, and personal growth. What would you like to talk about today?",
      isUser: false,
      timestamp: new Date(),
    },
  ]);

  const [error, setError] = useState<string | null>(null);
  const { sendMessage, isStreaming, currentResponse } = useChatStream();
  const { data: session } = useSession();
  const scrollRef = useRef<HTMLDivElement>(null);

  // Test function for debugging
  const testConnection = async () => {
    if (!session?.user?.id) {
      setError("Not authenticated");
      return;
    }

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/chat/test`,
        {
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
          body: JSON.stringify({ message: "Test connection" }),
        }
      );

      if (response.ok) {
        const result = await response.json();
        console.log("✅ Test connection successful:", result);
        setError(null);
        alert(`Test successful! Response: ${JSON.stringify(result, null, 2)}`);
      } else {
        const errorText = await response.text();
        console.error("❌ Test connection failed:", errorText);
        setError(`Test failed: ${response.status} ${response.statusText}`);
      }
    } catch (error) {
      console.error("❌ Test connection error:", error);
      setError(`Test error: ${error}`);
    }
  };

  const handleSendMessage = async (content: string) => {
    setError(null);

    const userMessage: Message = {
      id: Date.now().toString(),
      content,
      isUser: true,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);

    try {
      await sendMessage(
        content,
        sessionId,
        (aiMessage) => {
          setMessages((prev) => [...prev, aiMessage]);
        },
        (task) => {
          console.log("Task created:", task);
        }
      );
    } catch (error) {
      console.error("❌ Send message error:", error);
      if (error instanceof Error && error.message.includes("Authentication")) {
        setError("Authentication failed. Please sign in again.");
      } else {
        setError(error instanceof Error ? error.message : "An error occurred");
      }
    }
  };

  const handleSignOut = () => {
    signOut({ callbackUrl: "/auth/signin" });
  };

  // Auto-scroll to bottom
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, currentResponse]);

  return (
    <div className="flex flex-col h-full">
      {/* Header with Sign Out and Test Button */}
      <div className="border-b border-gray2/20 p-4 flex justify-between items-center">
        <h1 className="text-lg font-semibold text-white">Horizon AI Mentor</h1>
        <div className="flex gap-2">
          {process.env.NODE_ENV === "development" && (
            <Button
              variant="ghost"
              size="sm"
              onClick={testConnection}
              className="text-blue-400 hover:text-blue-300"
            >
              <TestTube className="h-4 w-4 mr-2" />
              Test
            </Button>
          )}
          <Button
            variant="ghost"
            size="sm"
            onClick={handleSignOut}
            className="text-gray1 hover:text-white"
          >
            <LogOut className="h-4 w-4 mr-2" />
            Sign Out
          </Button>
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <Alert variant="destructive" className="m-4 mb-0">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            <details>
              <summary className="cursor-pointer">Error Details</summary>
              <pre className="mt-2 text-xs overflow-auto">{error}</pre>
            </details>
          </AlertDescription>
        </Alert>
      )}

      {/* Session Info for Debugging */}
      {process.env.NODE_ENV === "development" && session && (
        <div className="bg-blue-900/20 p-2 m-4 rounded text-xs text-blue-200">
          <strong>Debug Info:</strong>
          <br />
          User ID: {session?.user?.id}
          <br />
          Email: {session?.user?.email}
          <br />
          Session ID: {sessionId || "None"}
        </div>
      )}

      {/* Chat Messages */}
      <ScrollArea className="flex-1 p-4">
        <div ref={scrollRef} className="space-y-4">
          <AnimatePresence>
            {messages.map((message) => (
              <ChatBubble key={message.id} message={message} />
            ))}
          </AnimatePresence>

          {/* Current AI Response */}
          {currentResponse && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex justify-start gap-3"
            >
              <ChatBubble
                message={{
                  id: "streaming",
                  content: currentResponse,
                  isUser: false,
                  timestamp: new Date(),
                }}
              />
            </motion.div>
          )}

          {/* Typing Indicator */}
          {isStreaming && !currentResponse && <TypingIndicator />}
        </div>
      </ScrollArea>

      {/* Chat Input */}
      <div className="border-t border-gray2/20 p-4">
        <ChatInput onSendMessage={handleSendMessage} disabled={isStreaming} />
      </div>
    </div>
  );
}
