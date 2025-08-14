"use client";

import React, { useState, useEffect } from "react";
import { Game } from "@/types/game";
import { apiClient } from "@/lib/api";
import WordleGrid from "@/components/wordle/WordleGrid";

export default function GamesPage() {
  // Get today's date in YYYY-MM-DD format (user's local timezone)
  const getTodayDate = () => {
    const today = new Date();
    const year = today.getFullYear();
    const month = String(today.getMonth() + 1).padStart(2, '0');
    const day = String(today.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  };

  const [games, setGames] = useState<Game[]>([]);
  const [selectedDate, setSelectedDate] = useState<string>(getTodayDate());
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadGames = async (date?: string) => {
    setIsLoading(true);
    setError(null);

    try {
      const gameData = await apiClient.getGamesByDate(date, true); // Include turns for WordleGrid
      setGames(gameData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load games");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    void loadGames(selectedDate);
  }, [selectedDate]);

  const handleDateChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const newDate = event.target.value;
    setSelectedDate(newDate);
    // useEffect will automatically call loadGames when selectedDate changes
  };

  return (
    <div className="container mx-auto px-4 py-8">
      {/*  Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-[var(--color-text)] mb-4">Individual Games</h1>
        <p className="text-[var(--color-text-secondary)] mb-6">
          View detailed Wordle game results with reasoning for each guess.
        </p>

        {/* Date picker */}
        <div className="mb-6 p-4 bg-[var(--color-section-background)] rounded-lg border border-[var(--color-border)]">
          <label htmlFor="game-date" className="block text-sm font-medium text-[var(--color-text)] mb-2">
            Select Date
          </label>
          <input
            id="game-date"
            type="date"
            value={selectedDate}
            onChange={handleDateChange}
            className="px-3 py-2 border border-[var(--color-border)] rounded-md text-[var(--color-text)] bg-[var(--color-background)]"
          />
        </div>
      </div>

      {/* Loading state */}
      {isLoading && (
        <div className="text-center py-8">
          <p className="text-[var(--color-text-secondary)]">Loading games...</p>
        </div>
      )}

      {/* Error state */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <p className="text-red-700">Unable to load games. Please try again.</p>
          <button
            onClick={() => loadGames(selectedDate)}
            className="mt-2 text-sm text-red-600 hover:text-red-800 underline"
          >
            Try again
          </button>
        </div>
      )}

      {/* Empty state */}
      {!isLoading && games.length === 0 && !error && (
        <div className="text-center py-8">
          <p className="text-[var(--color-text-secondary)]">
            {selectedDate ? `No games found for ${selectedDate}` : "No games available. Select a date to view games."}
          </p>
        </div>
      )}

      {/* Games grid */}
      {!isLoading && games.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {games.map(game => (
            <div
              key={game.id}
              className="bg-[var(--color-section-background)] rounded-lg p-6 border border-[var(--color-border)]"
            >
              <div className="mb-4">
                <h3 className="font-semibold text-[var(--color-text)] mb-2">{game.model_name}</h3>
                <p className="text-sm text-[var(--color-text-secondary)]">
                  Target: {game.target_word.toUpperCase()} • {game.won ? `Won in ${game.guesses_count}` : "Lost"} •{" "}
                  {game.duration_seconds.toFixed(1)}s
                </p>
                <div className="mt-2 flex gap-2 text-xs text-[var(--color-text-secondary)]">
                  <span>Template: {game.template_name}</span>
                  <span>Parser: {game.parser_name}</span>
                </div>
              </div>

              {/* Wordle Grid */}
              <div className="mb-4">
                <p className="text-xs text-[var(--color-text-secondary)] mb-2">
                  {game.guesses_count} guesses • Status: {game.status}
                </p>
                {game.turns && game.turns.length > 0 ? (
                  <div className="flex justify-center">
                    <WordleGrid turns={game.turns} maxTurns={6} />
                  </div>
                ) : (
                  <div className="w-full h-16 bg-[var(--color-border)] rounded opacity-50 flex items-center justify-center">
                    <span className="text-xs text-[var(--color-text-secondary)]">No turn data</span>
                  </div>
                )}
              </div>

              <button
                onClick={() => {
                  // TODO: Navigate to game details page or show modal
                  console.log("Show details for game:", game.id);
                }}
                className="text-sm text-[var(--color-primary)] hover:text-[var(--color-accent)] transition-colors"
              >
                Show details →
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
