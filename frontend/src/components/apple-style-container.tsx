// components/AppleStyleContainer.tsx
"use client";

import React, { useRef } from "react";
import { motion } from "framer-motion";
import AppleStyleButton from "./apple-style-button";

interface AppleStyleContainerProps {
  backgroundColor?: string;
  children?: React.ReactNode;
  buttonProps?: {
    text?: string;
    colorScheme?: "mint" | "lemon" | "mist";
    size?: "sm" | "md" | "lg";
    onClick?: () => void;
  };
}

const AppleStyleContainer: React.FC<AppleStyleContainerProps> = ({
  backgroundColor = "#ffea96",
  children,
  buttonProps = {},
}) => {
  const containerRef = useRef<HTMLDivElement>(null);

  const {
    text = "start",
    colorScheme = "lemon",
    size = "md",
    onClick = () => console.log("Button clicked!"),
  } = buttonProps;

  return (
    <motion.div
      ref={containerRef}
      className="w-full flex-1 max-w-4xl aspect-video rounded-[28px] flex items-center justify-center overflow-hidden"
      style={{ backgroundColor }}
      initial={{ opacity: 0, y: 20 }}
      animate={{
        opacity: 1,
        y: 0,
        boxShadow: "0 10px 30px rgba(0,0,0,0.1), 0 1px 8px rgba(0,0,0,0.05)",
      }}
      transition={{ duration: 0.6, ease: "easeOut" }}
      whileHover={{
        boxShadow: "0 15px 30px rgba(0,0,0,0.15), 0 1px 12px rgba(0,0,0,0.1)",
      }}
    >
      {children || (
        <AppleStyleButton
          text={text}
          colorScheme={colorScheme}
          size={size}
          onClick={onClick}
          containerRef={containerRef}
        />
      )}
    </motion.div>
  );
};

export default AppleStyleContainer;
