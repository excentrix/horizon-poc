// frontend/src/components/chat/chat-area.tsx (update imports and usage)
"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ChatBubble } from "./chat-bubble";
import { ChatInput } from "./chat-input";
import { TypingIndicator } from "./typing-indicator";
import { useChatStreamV2 } from "@/hooks/use-chat-stream-v2"; // Changed to v2
import { AlertTriangle, LogOut, TestTube, Zap } from "lucide-react";
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
        "Hello! I'm Horizon, your enhanced AI learning mentor. I now have improved memory and can provide more personalized guidance. What would you like to talk about today?",
      isUser: false,
      timestamp: new Date(),
    },
  ]);

  const [error, setError] = useState<string | null>(null);
  const { sendMessage, isStreaming, currentResponse } = useChatStreamV2(); // Using v2
  const { data: session } = useSession();
  const scrollRef = useRef<HTMLDivElement>(null);

  // Test v2 connection
  const testV2Connection = async () => {
    if (!session?.user?.id) {
      setError("Not authenticated");
      return;
    }

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v2/test`,
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
        }
      );

      if (response.ok) {
        const result = await response.json();
        console.log("✅ v2 Test successful:", result);
        setError(null);
        alert(
          `v2 System Working! Features: ${JSON.stringify(result, null, 2)}`
        );
      } else {
        const errorText = await response.text();
        console.error("❌ v2 Test failed:", errorText);
        setError(`v2 Test failed: ${response.status}`);
      }
    } catch (error) {
      console.error("❌ v2 Test error:", error);
      setError(`v2 Test error: ${error}`);
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
      await sendMessage(content, sessionId, (aiMessage) => {
        setMessages((prev) => [...prev, aiMessage]);
      });
    } catch (error) {
      console.error("❌ v2 Send message error:", error);
      setError(error instanceof Error ? error.message : "An error occurred");
    }
  };

  const handleSignOut = () => {
    signOut({ callbackUrl: "/auth/signin" });
  };

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, currentResponse]);

  return (
    <div className="flex flex-col h-full">
      {/* Header with v2 indicator */}
      <div className="border-b border-gray2/20 p-4 flex justify-between items-center">
        <div className="flex items-center gap-3">
          <h1 className="text-lg font-semibold text-white">
            Horizon AI Mentor
          </h1>
          <Badge
            variant="secondary"
            className="bg-green-900/20 text-green-400 border-green-500/30"
          >
            <Zap className="h-3 w-3 mr-1" />
            Enhanced v2
          </Badge>
        </div>
        <div className="flex gap-2">
          {process.env.NODE_ENV === "development" && (
            <Button
              variant="ghost"
              size="sm"
              onClick={testV2Connection}
              className="text-blue-400 hover:text-blue-300"
            >
              <TestTube className="h-4 w-4 mr-2" />
              Test v2
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
              <summary className="cursor-pointer">v2 System Error</summary>
              <pre className="mt-2 text-xs overflow-auto">{error}</pre>
            </details>
          </AlertDescription>
        </Alert>
      )}

      {/* Debug Info */}
      {process.env.NODE_ENV === "development" && session && (
        <div className="bg-green-900/20 p-2 m-4 rounded text-xs text-green-200">
          <strong>v2 System Active:</strong>
          <br />
          API: /api/v2/chat/stream
          <br />
          User: {session?.user?.email}
          <br />
          Session: {sessionId || "None"}
          <br />
          Features: Enhanced Memory, Agent-based, Prompt Management
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
        <ChatInput
          onSendMessage={handleSendMessage}
          disabled={isStreaming}
        //   placeholder="Message Horizon (Enhanced v2)..."
        />
      </div>
    </div>
  );
}
