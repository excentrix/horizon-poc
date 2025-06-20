// frontend/src/components/chat/chat-area.tsx
"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { ChatBubble } from "./chat-bubble";
import { ChatInput } from "./chat-input";
import { TypingIndicator } from "./typing-indicator";
import { useChatStream } from "@/hooks/use-chat-stream";
import { AlertTriangle } from "lucide-react";

interface Message {
  id: string;
  content: string;
  isUser: boolean;
  timestamp: Date;
}

interface ChatAreaProps {
  sessionId: string | null;
  onSessionChange: (sessionId: string) => void;
  userEmail: string;
}

export function ChatArea({
  sessionId,
  onSessionChange,
  userEmail,
}: ChatAreaProps) {
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
  const scrollRef = useRef<HTMLDivElement>(null);

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
        userEmail,
        (aiMessage) => {
          setMessages((prev) => [...prev, aiMessage]);
        },
        (task) => {
          console.log("Task created:", task);
        }
      );
    } catch (error) {
      setError(error instanceof Error ? error.message : "An error occurred");
    }
  };

  // Auto-scroll to bottom
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, currentResponse]);

  return (
    <div className="flex flex-col h-full overflow-y-auto scroll-auto">
      {/* Error Alert */}
      {error && (
        <Alert variant="destructive" className="m-4 mb-0">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
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
