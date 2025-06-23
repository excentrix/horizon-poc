// components/AppleStyleButton.tsx
"use client";

import React, { useRef, useState, useEffect } from "react";
import { motion } from "framer-motion";
import Color from "color";

interface AppleStyleButtonProps {
  onClick?: () => void;
  text?: string;
  size?: "sm" | "md" | "lg";
  colorScheme?: "mint" | "lemon" | "mist";
  containerRef?: React.RefObject<HTMLDivElement>;
}

const AppleStyleButton: React.FC<AppleStyleButtonProps> = ({
  onClick,
  text = "start",
  size = "md",
  colorScheme = "lemon",
  containerRef,
}) => {
  // Mouse tracking state
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  const [isHovered, setIsHovered] = useState(false);
  const [isPressed, setIsPressed] = useState(false);
  const buttonRef = useRef<HTMLDivElement>(null);

  // Generate color variations based on the base color
  const getColors = (baseColorHex: string) => {
    const baseColor = Color(baseColorHex);

    return {
      lighter: baseColor.lighten(0.2).hex(),
      light: baseColor.lighten(0.1).hex(),
      base: baseColor.hex(),
      dark: baseColor.darken(0.1).hex(),
      darker: baseColor.darken(0.2).hex(),
      darkest: baseColor.darken(0.3).hex(),
      // For text and shadows
      contrastText: baseColor.isDark() ? "#ffffff" : "#242424",
      shadow: baseColor.darken(0.3).alpha(0.5).toString(),
    };
  };

  // Color map with base colors
  const colorMap = {
    mint: getColors("#b0e9f2"),
    lemon: getColors("#ffea96"),
    mist: getColors("#cceab7"),
  };

  const colors = colorMap[colorScheme];

  // Size configuration
  const sizes = {
    sm: { button: "w-20 h-20", text: "text-xs", trackRange: 5 },
    md: { button: "w-32 h-32", text: "text-sm", trackRange: 8 },
    lg: { button: "w-52 h-52", text: "text-base", trackRange: 10 },
  };

  const selectedSize = sizes[size];
  const trackingRange = selectedSize.trackRange;

  // Mouse tracking within container
  useEffect(() => {
    if (!containerRef?.current) return;

    const container = containerRef.current;

    const handleMouseMove = (e: MouseEvent) => {
      const rect = container.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;

      setMousePosition({ x, y });
    };

    container.addEventListener("mousemove", handleMouseMove);
    return () => {
      container.removeEventListener("mousemove", handleMouseMove);
    };
  }, [containerRef]);

  // Calculate button position based on mouse
  const calculateButtonOffset = () => {
    if (!buttonRef.current || !containerRef?.current || !isHovered)
      return { x: 0, y: 0 };

    const buttonRect = buttonRef.current.getBoundingClientRect();
    const containerRect = containerRef.current.getBoundingClientRect();

    // Button center position
    const buttonCenterX =
      buttonRect.left + buttonRect.width / 2 - containerRect.left;
    const buttonCenterY =
      buttonRect.top + buttonRect.height / 2 - containerRect.top;

    // Calculate direction from button center to mouse
    const deltaX = mousePosition.x - buttonCenterX;
    const deltaY = mousePosition.y - buttonCenterY;

    // Scale the movement to be subtle
    const maxMove = trackingRange;
    const scaleFactor = 0.15;

    return {
      x: Math.max(Math.min(deltaX * scaleFactor, maxMove), -maxMove),
      y: Math.max(Math.min(deltaY * scaleFactor, maxMove), -maxMove),
    };
  };

  const buttonOffset = calculateButtonOffset();

  return (
    <div ref={buttonRef} className="relative">
      {/* Main Button Container with subtle tracking movement */}
      <motion.div
        className={`relative ${selectedSize.button} cursor-pointer`}
        animate={{
          x: buttonOffset.x,
          y: buttonOffset.y,
          scale: isPressed ? 0.97 : isHovered ? 1.02 : 1,
        }}
        transition={{
          type: "spring",
          stiffness: 400,
          damping: 25,
        }}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => {
          setIsHovered(false);
          setIsPressed(false);
        }}
        onMouseDown={() => setIsPressed(true)}
        onMouseUp={() => setIsPressed(false)}
        onClick={onClick}
      >
        {/* Shadow/glow effect */}
        <motion.div
          className="absolute inset-0 rounded-full blur-md"
          style={{ backgroundColor: colors.shadow }}
          animate={{
            opacity: isHovered ? 0.7 : 0.3,
            scale: isHovered ? 1.05 : 1,
          }}
          transition={{ duration: 0.3 }}
        />

        {/* Outermost ring - pulsing */}
        <motion.div
          className="absolute inset-0 rounded-full"
          style={{ backgroundColor: colors.lighter }}
          animate={{
            scale: [1, 1.1, 1],
            opacity: [0.4, 0.2, 0.4],
          }}
          transition={{
            repeat: Infinity,
            duration: 3,
            ease: "easeInOut",
          }}
        />

        {/* Middle outer ring - subtle pulse */}
        <motion.div
          className="absolute inset-[4px] rounded-full"
          style={{ backgroundColor: colors.light }}
          animate={{
            scale: [1, 1.05, 1],
            opacity: [0.6, 0.4, 0.6],
          }}
          transition={{
            repeat: Infinity,
            duration: 4,
            ease: "easeInOut",
            delay: 0.5,
          }}
        />

        {/* Middle inner ring - mostly static with subtle breathing */}
        <motion.div
          className="absolute inset-[8px] rounded-full"
          style={{ backgroundColor: colors.base }}
          animate={{
            scale: [1, 1.02, 1],
            opacity: [0.8, 0.7, 0.8],
          }}
          transition={{
            repeat: Infinity,
            duration: 5,
            ease: "easeInOut",
            delay: 1,
          }}
        />

        {/* Inner circle - main button area */}
        <motion.div
          className="absolute inset-[12px] rounded-full flex items-center justify-center"
          style={{
            backgroundColor: colors.dark,
            boxShadow: `inset 0 2px 4px rgba(0,0,0,0.1), 0 1px 2px rgba(255,255,255,0.1)`,
          }}
          animate={{
            scale: isPressed ? 0.98 : [0.98, 1.02, 0.98],
          }}
          transition={
            isPressed
              ? { duration: 0.2 }
              : {
                  repeat: Infinity,
                  duration: 2,
                  ease: "easeInOut",
                }
          }
        >
          {/* Text with subtle floating effect */}
          <motion.span
            className={`font-medium ${selectedSize.text}`}
            style={{ color: colors.contrastText }}
            animate={{
              y: isPressed ? 1 : [-1, 1, -1],
              opacity: isPressed ? 0.9 : 1,
            }}
            transition={
              isPressed
                ? { duration: 0.2 }
                : {
                    repeat: Infinity,
                    duration: 2.5,
                    ease: "easeInOut",
                  }
            }
          >
            {text}
          </motion.span>
        </motion.div>
      </motion.div>
    </div>
  );
};

export default AppleStyleButton;
