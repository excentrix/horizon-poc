// frontend/src/components/chat/chat-input.tsx
"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Send } from "lucide-react";

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  disabled?: boolean;
}

export function ChatInput({ onSendMessage, disabled }: ChatInputProps) {
  const [message, setMessage] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim() || disabled) return;

    onSendMessage(message.trim());
    setMessage("");
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex gap-2">
      <Textarea
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Type your message... (Enter to send, Shift+Enter for new line)"
        className="min-h-[44px] max-h-32 resize-none bg-gray2/10 border-gray2/20 text-white placeholder:text-gray1"
        disabled={disabled}
      />
      <Button
        type="submit"
        size="icon"
        className="h-11 w-11 bg-mint hover:bg-mint/80 text-dark"
        disabled={disabled || !message.trim()}
      >
        <Send className="h-4 w-4" />
      </Button>
    </form>
  );
}
