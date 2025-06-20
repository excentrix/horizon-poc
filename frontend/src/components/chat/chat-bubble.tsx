// frontend/src/components/chat/chat-bubble.tsx
"use client";

import { motion } from "framer-motion";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";

interface Message {
  id: string;
  content: string;
  isUser: boolean;
  timestamp: Date;
}

interface ChatBubbleProps {
  message: Message;
}

export function ChatBubble({ message }: ChatBubbleProps) {
  return (
    <motion.div
      initial={{ y: 8, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.25, ease: "easeOut" }}
      className={`flex ${
        message.isUser ? "justify-end" : "justify-start"
      } gap-3`}
    >
      {!message.isUser && (
        <Avatar className="h-8 w-8 mt-1">
          <AvatarFallback className="bg-mint text-dark text-xs font-semibold">
            HZ
          </AvatarFallback>
        </Avatar>
      )}

      <div
        className={`max-w-[80%] md:max-w-md rounded-lg p-3 ${
          message.isUser ? "bg-mint text-dark" : "bg-gray2/20 text-white"
        }`}
      >
        <p className="text-sm leading-relaxed">{message.content}</p>
        <span className="text-xs opacity-70 mt-1 block">
          {message.timestamp.toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          })}
        </span>
      </div>

      {message.isUser && (
        <Avatar className="h-8 w-8 mt-1">
          <AvatarFallback className="bg-lemon text-dark text-xs font-semibold">
            U
          </AvatarFallback>
        </Avatar>
      )}
    </motion.div>
  );
}
