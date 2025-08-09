import { GameTurn, LetterResult } from "@/types/api";
import LetterTile from "./LetterTile";
import { useState, useEffect } from "react";

interface WordleGridProps {
  turns: GameTurn[];
  maxTurns?: number;
}

export default function WordleGrid({ turns, maxTurns = 6 }: Readonly<WordleGridProps>) {
  const [animateIn, setAnimateIn] = useState(false);

  useEffect(() => {
    if (turns.length > 0) {
      // Start animation immediately - tiles are hidden until they animate in
      setAnimateIn(true);
    }
  }, [turns]);

  const renderTurn = (turn: GameTurn) => (
    <div key={turn.turn_number} className="wordle-row flex gap-1 mb-1">
      {turn.letter_results.map((letterResult: LetterResult) => (
        <LetterTile
          key={letterResult.position}
          letter={letterResult.letter}
          status={letterResult.status}
          position={letterResult.position}
          animateIn={animateIn}
        />
      ))}
    </div>
  );

  const renderEmptyTurn = (turnNumber: number) => (
    <div key={`empty-${turnNumber}`} className="wordle-row flex gap-1 mb-1">
      {Array.from({ length: 5 }, (_, index) => (
        <div key={index} className="w-14 h-14 border-2 border-gray-300 rounded flex items-center justify-center" />
      ))}
    </div>
  );

  return (
    <div className="wordle-grid" role="grid" aria-label="Wordle game grid">
      {Array.from({ length: maxTurns }, (_, index) => {
        const turn = turns.find(t => t.turn_number === index + 1);
        return turn ? renderTurn(turn) : renderEmptyTurn(index + 1);
      })}
    </div>
  );
}
