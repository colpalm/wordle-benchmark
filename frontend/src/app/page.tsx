"use client";

import { useLeaderboard } from "@/hooks/useLeaderboard";
import { LeaderboardTable } from "@/components/LeaderboardTable";

export default function HomePage() {
  const { data, metadata, loading, error, sortConfig, sortBy } = useLeaderboard();

  const calculateAvgWinRate = (): number => {
    if (!data.length) return 0;
    const totalWinRate = data.reduce((sum, entry) => sum + entry.win_rate, 0);
    return totalWinRate / data.length;
  };

  const calculateAvgGuesses = (): number => {
    const validEntries = data.filter(e => e.avg_guesses != null);
    if (validEntries.length === 0) return 0;
    const total = validEntries.reduce((sum, entry) => sum + (entry.avg_guesses ?? 0), 0);
    return total / validEntries.length;
  };

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header Section */}
      <div className="mb-8 text-center">
        <h1 className="text-4xl font-bold text-[var(--color-text)] mb-4">LLM Word(le) Performance Leaderboard</h1>
        <p className="text-lg text-[var(--color-text-secondary)] mb-6 max-w-2xl mx-auto">
          Comparing how Large Language Models perform at NYT's Wordle&reg;. Updated daily with new games.
        </p>
        <p className="text-sm text-[var(--color-text-secondary)] mb-6 max-w-2xl mx-auto opacity-75 font-bold">
          This is an unofficial research project and is not associated with or endorsed by The New York Times.
        </p>

        {/* Quick Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-2xl mx-auto">
          <div className="bg-[var(--color-section-background)] rounded-lg p-4 border border-[var(--color-border)]">
            <div className="text-2xl font-bold text-[var(--color-primary)]">
              {loading ? "..." : metadata?.total_games || 0}
            </div>
            <div className="text-sm text-[var(--color-text-secondary)]">Total Games</div>
          </div>
          <div className="bg-[var(--color-section-background)] rounded-lg p-4 border border-[var(--color-border)]">
            <div className="text-2xl font-bold text-[var(--color-primary)]">
              {loading ? "..." : metadata?.total_models || 0}
            </div>
            <div className="text-sm text-[var(--color-text-secondary)]">Models</div>
          </div>
          <div className="bg-[var(--color-section-background)] rounded-lg p-4 border border-[var(--color-border)]">
            <div className="text-2xl font-bold text-[var(--color-primary)]">
              {loading ? "..." : `${calculateAvgWinRate().toFixed(1)}%`}
            </div>
            <div className="text-sm text-[var(--color-text-secondary)]">Avg Win Rate</div>
          </div>
          <div className="bg-[var(--color-section-background)] rounded-lg p-4 border border-[var(--color-border)]">
            <div className="text-2xl font-bold text-[var(--color-primary)]">
              {loading ? "..." : calculateAvgGuesses().toFixed(1)}
            </div>
            <div className="text-sm text-[var(--color-text-secondary)]">Avg Guesses</div>
          </div>
        </div>
      </div>

      {/* Leaderboard Table */}
      <LeaderboardTable data={data} loading={loading} error={error} sortConfig={sortConfig} onSort={sortBy} />

      {/* Last Updated */}
      <div className="mt-6 text-center text-sm text-[var(--color-text-secondary)]">
        {metadata?.last_updated
          ? `Last updated: ${new Date(metadata.last_updated).toLocaleDateString()} • Next update at 3:00 AM PT`
          : "Loading update information..."}
      </div>
    </div>
  );
}
