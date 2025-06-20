// frontend/src/components/chat/typing-indicator.tsx
"use client";

import { motion } from "framer-motion";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";

export function TypingIndicator() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className="flex justify-start gap-3"
    >
      <Avatar className="h-8 w-8 mt-1">
        <AvatarFallback className="bg-mint text-dark text-xs font-semibold">
          HZ
        </AvatarFallback>
      </Avatar>

      <div className="bg-gray2/20 rounded-lg p-3 max-w-xs">
        <div className="flex space-x-1">
          <motion.div
            className="w-2 h-2 bg-mint rounded-full"
            animate={{ y: [0, -4, 0] }}
            transition={{
              duration: 0.6,
              repeat: Infinity,
              repeatType: "loop",
            }}
          />
          <motion.div
            className="w-2 h-2 bg-mint rounded-full"
            animate={{ y: [0, -4, 0] }}
            transition={{
              duration: 0.6,
              repeat: Infinity,
              repeatType: "loop",
              delay: 0.1,
            }}
          />
          <motion.div
            className="w-2 h-2 bg-mint rounded-full"
            animate={{ y: [0, -4, 0] }}
            transition={{
              duration: 0.6,
              repeat: Infinity,
              repeatType: "loop",
              delay: 0.2,
            }}
          />
        </div>
      </div>
    </motion.div>
  );
}
