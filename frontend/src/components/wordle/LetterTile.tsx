import { LetterResult, LetterStatus } from "@/types/api";

interface LetterTileProps extends LetterResult {
  animateIn?: boolean;
}

export default function LetterTile({ letter, status, position, animateIn = false }: Readonly<LetterTileProps>) {
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

  return (
    <div
      className={`
        w-14 h-14 border-2 rounded flex items-center justify-center
        font-bold text-lg uppercase transition-all duration-200
        ${getStatusClasses()}
        ${animateIn ? "tile-animate-in" : ""}
      `}
      data-position={position}
      aria-label={`Letter ${letter} at position ${position + 1}, status: ${status}`}
    >
      {letter}
    </div>
  );
}
