import { LetterResult, LetterStatus } from "@/types/api";
import React, { useState, useCallback } from "react";

interface LetterTileProps extends LetterResult {
  animateIn?: boolean;
}

const ANIMATION_DELAY_MS = 100;

export default function LetterTile({ letter, status, position, animateIn = false }: Readonly<LetterTileProps>) {
  const [finished, setFinished] = useState(false);

  const getStatusClasses = () => {
    switch (status) {
      case LetterStatus.CORRECT:
        return "bg-wordle-green text-white border-wordle-green";
      case LetterStatus.PRESENT:
        return "bg-wordle-yellow text-white border-wordle-yellow";
      case LetterStatus.ABSENT:
        return "bg-gray-600 text-white border-gray-600";
      default:
        return "bg-white text-black border-gray-300";
    }
  };

  const handleAnimationEnd = useCallback(() => {
    // Lock the tile into its final state and remove the animation to prevent Safari flicker
    setFinished(true);
  }, []);

  const delayMs = position * ANIMATION_DELAY_MS;

  const getAnimationStyles = () => {
    if (finished) {
      return {
        animation: "none",
        transform: "translateZ(0) rotateX(0deg)",
        opacity: 1,
        willChange: "auto",
      };
    }
    
    if (animateIn && !finished) {
      return { animationDelay: `${delayMs}ms` };
    }
    
    return {};
  };

  return (
    <div className="tile-wrapper w-14 h-14">
      <div
        className={`
          tile-inner w-full h-full border-2 rounded flex items-center justify-center
          font-bold text-lg uppercase
          ${getStatusClasses()}
          ${animateIn && !finished ? "tile-animate-in" : ""}
        `}
        style={getAnimationStyles()}
        onAnimationEnd={handleAnimationEnd}
        data-position={position}
        aria-label={`Letter ${letter} at position ${position + 1}, status: ${status}`}
      >
        {letter}
      </div>
    </div>
  );
}
