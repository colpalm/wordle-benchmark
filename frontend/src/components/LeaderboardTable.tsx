import { LeaderboardEntry, SortConfig, SortColumn } from "@/types/leaderboard";

type ColorThreshold = {
  condition: (value: number) => boolean;
  colorClass: string;
};

interface LeaderboardTableProps {
  data: LeaderboardEntry[];
  loading: boolean;
  error: string | null;
  sortConfig: SortConfig;
  onSort: (column: SortColumn) => void;
}

const getTrophy = (index: number): string => {
  switch (index) {
    case 0:
      return "🥇";
    case 1:
      return "🥈";
    case 2:
      return "🥉";
    default:
      return "";
  }
};

const formatWinRate = (entry: LeaderboardEntry): string => {
  return `${entry.win_rate.toFixed(1)}% (${entry.wins}/${entry.total_games})`;
};

const formatGolfScore = (score: number): string => {
  if (score > 0) return `+${score}`;
  if (score < 0) return `${score}`;
  return "0";
};

const formatRecentResults = (recentResults: LeaderboardEntry["recent_results"]): string => {
  // Show actual games, most recent first
  return recentResults
    .slice()
    .reverse()
    .map(game => (game.won ? "✅" : "❌"))
    .join(" ");
};

const getColorClass = (value: number, thresholds: ColorThreshold[]): string => {
  for (const threshold of thresholds) {
    if (threshold.condition(value)) {
      return threshold.colorClass;
    }
  }
  return "text-[var(--color-text)]"; // default
};

const winRateThresholds: ColorThreshold[] = [
  { condition: (rate) => rate >= 80, colorClass: "text-green-600" },
  { condition: (rate) => rate >= 65, colorClass: "text-yellow-600" },
  { condition: () => true, colorClass: "text-gray-500" } // fallback
];

const golfScoreThresholds: ColorThreshold[] = [
  { condition: (score) => score < 0, colorClass: "text-green-600" },
  { condition: (score) => score > 0, colorClass: "text-red-600" },
  { condition: () => true, colorClass: "text-[var(--color-text)]" } // fallback for 0
];

const getSortIcon = (column: SortColumn, sortConfig: SortConfig): string => {
  if (sortConfig.column !== column) return "";
  return sortConfig.direction === "desc" ? " ↓" : " ↑";
};

export function LeaderboardTable({ data, loading, error, sortConfig, onSort }: Readonly<LeaderboardTableProps>) {
  if (error) {
    return (
      <div className="bg-[var(--color-section-background)] rounded-lg border border-[var(--color-border)] p-8 text-center">
        <p className="text-[var(--color-text-secondary)]">{error}</p>
        <button
          onClick={() => window.location.reload()}
          className="mt-4 px-4 py-2 bg-[var(--color-primary)] text-white rounded hover:opacity-80 transition-opacity"
        >
          Try Again
        </button>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="bg-[var(--color-section-background)] rounded-lg border border-[var(--color-border)] overflow-hidden">
        <div className="px-6 py-4 border-b border-[var(--color-border)]">
          <h2 className="text-xl font-semibold text-[var(--color-text)]">Model Performance Rankings</h2>
        </div>
        <div className="p-8 text-center">
          <p className="text-[var(--color-text-secondary)]">Loading leaderboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-[var(--color-section-background)] rounded-lg border border-[var(--color-border)] overflow-hidden">
      <div className="px-6 py-4 border-b border-[var(--color-border)]">
        <h2 className="text-xl font-semibold text-[var(--color-text)]">Model Performance Rankings</h2>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-[var(--color-background)]">
            <tr className="text-left">
              <th
                className="px-6 py-4 text-sm font-bold text-[var(--color-text)] border-b border-[var(--color-border)] cursor-pointer hover:bg-[var(--color-section-background)] transition-colors"
                onClick={() => onSort("model_name")}
              >
                Model{getSortIcon("model_name", sortConfig)}
              </th>
              <th
                className="px-6 py-4 text-sm font-bold text-[var(--color-text)] border-b border-[var(--color-border)] cursor-pointer hover:bg-[var(--color-section-background)] transition-colors"
                onClick={() => onSort("win_rate")}
              >
                Win Rate{getSortIcon("win_rate", sortConfig)}
              </th>
              <th
                className="px-6 py-4 text-sm font-bold text-[var(--color-text)] border-b border-[var(--color-border)] cursor-pointer hover:bg-[var(--color-section-background)] transition-colors"
                onClick={() => onSort("avg_guesses")}
              >
                Avg Guesses{getSortIcon("avg_guesses", sortConfig)}
              </th>
              <th
                className="px-6 py-4 text-sm font-bold text-[var(--color-text)] border-b border-[var(--color-border)] cursor-pointer hover:bg-[var(--color-section-background)] transition-colors"
                onClick={() => onSort("total_golf_score")}
              >
                Golf Score{getSortIcon("total_golf_score", sortConfig)}
              </th>
              <th
                className="px-6 py-4 text-sm font-bold text-[var(--color-text)] border-b border-[var(--color-border)] cursor-pointer hover:bg-[var(--color-section-background)] transition-colors"
                onClick={() => onSort("recent_results")}
              >
                Recent Results{getSortIcon("recent_results", sortConfig)}
              </th>
            </tr>
          </thead>
          <tbody>
            {data.map((entry, index) => (
              <tr key={entry.model_name} className="hover:bg-[var(--color-background)] transition-colors">
                <td className="px-6 py-5 text-sm font-medium text-[var(--color-text)] border-b border-[var(--color-border)]">
                  <span className="mr-2">{getTrophy(index)}</span>
                  {entry.model_name}
                </td>
                <td className="px-6 py-5 text-sm text-[var(--color-text)] border-b border-[var(--color-border)]">
                  <span className={`font-semibold ${getColorClass(entry.win_rate, winRateThresholds)}`}>
                    {formatWinRate(entry)}
                  </span>
                </td>
                <td className="px-6 py-5 text-sm text-[var(--color-text)] border-b border-[var(--color-border)]">
                  {entry.avg_guesses?.toFixed(1) || "N/A"}
                </td>
                <td className="px-6 py-5 text-sm text-[var(--color-text)] border-b border-[var(--color-border)]">
                  <span className={`font-semibold ${getColorClass(entry.total_golf_score, golfScoreThresholds)}`}>
                    {formatGolfScore(entry.total_golf_score)}
                  </span>
                </td>
                <td className="px-6 py-5 border-b border-[var(--color-border)]">
                  <span className="font-mono text-sm">{formatRecentResults(entry.recent_results)}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
