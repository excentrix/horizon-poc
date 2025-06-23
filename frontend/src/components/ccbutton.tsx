// components/ConcentricCirclesButton.tsx
"use client";

import React from "react";

interface ConcentricCirclesButtonProps {
  onClick?: () => void;
  text?: string;
  size?: "sm" | "md" | "lg";
  colorScheme?: "mint" | "lemon" | "mist";
  variant?: "standard" | "staggered";
}

const ConcentricCirclesButton: React.FC<ConcentricCirclesButtonProps> = ({
  onClick,
  text = "start",
  size = "md",
  colorScheme = "lemon",
  variant = "standard",
}) => {
  // Size configuration
  const buttonSizeClass = `concentric-button-${size}`;
  const textSizeClass = `concentric-text-${size}`;

  // Animation variant
  const animationClass =
    variant === "staggered"
      ? "animate-pulse-ring-staggered"
      : "animate-pulse-ring";

  // Color configuration based on your design system
  const colorMap = {
    mint: {
      light: "#b0e9f2",
      medium: "#8cd9e5",
      dark: "#68c9d8",
      darker: "#44b9cb",
      text: "#242424", // using your dark color for text
    },
    lemon: {
      light: "#b2a369",
      medium: "#ccbb78",
      dark: "#e5d287",
      darker: "#ffea96",
      text: "#242424", // using your dark color for text
    },
    mist: {
      light: "#cceab7",
      medium: "#b9e099",
      dark: "#a6d67b",
      darker: "#93cc5d",
      text: "#242424", // using your dark color for text
    },
  };

  const colors = colorMap[colorScheme];

  return (
    <button
      className={`concentric-button ${buttonSizeClass}`}
      aria-label={text}
      onClick={onClick}
    >
      {/* Outermost ring - animated */}
      <div
        className={`absolute inset-0 rounded-full opacity-20 ${animationClass}`}
        style={{ backgroundColor: colors.light }}
      ></div>

      {/* Middle ring - static */}
      <div
        className="absolute inset-2 rounded-full opacity-50"
        style={{ backgroundColor: colors.medium }}
      ></div>

      {/* Middle-inner ring - static */}
      <div
        className="absolute inset-4 rounded-full opacity-70"
        style={{ backgroundColor: colors.dark }}
      ></div>

      {/* Inner circle - animated */}
      <div
        className="absolute inset-6 rounded-full flex items-center justify-center animate-pulse-dot"
        style={{ backgroundColor: colors.darker }}
      >
        <span
          className={`font-bold ${textSizeClass}`}
          style={{ color: colors.text }}
        >
          {text}
        </span>
      </div>
    </button>
  );
};

export default ConcentricCirclesButton;


