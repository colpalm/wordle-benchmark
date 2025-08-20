import { useState, useEffect, useMemo } from "react";
import { LeaderboardResponse, LeaderboardEntry, SortConfig, SortColumn } from "@/types/leaderboard";
import { apiClient } from "@/lib/api";

interface UseLeaderboardResult {
  data: LeaderboardEntry[];
  metadata: LeaderboardResponse["metadata"] | null;
  loading: boolean;
  error: string | null;
  sortConfig: SortConfig;
  sortBy: (column: SortColumn) => void;
  refresh: () => void;
}

export function useLeaderboard(): UseLeaderboardResult {
  const [rawData, setRawData] = useState<LeaderboardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sortConfig, setSortConfig] = useState<SortConfig>({
    column: "win_rate",
    direction: "desc",
  });

  const fetchLeaderboard = async () => {
    try {
      setLoading(true);
      setError(null);

      const data = await apiClient.getLeaderboard();
      setRawData(data);
    } catch (err) {
      setError("Unable to retrieve leaderboard data. Please try again.");
      console.error("Leaderboard fetch error:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void fetchLeaderboard();
  }, []);

  const sortedData = useMemo(() => {
    if (!rawData?.leaderboard) return [];

    const sorted = [...rawData.leaderboard].sort((a, b) => {
      let aVal: string | number;
      let bVal: string | number;

      switch (sortConfig.column) {
        case "model_name":
          aVal = a.model_name.toLowerCase();
          bVal = b.model_name.toLowerCase();
          break;
        case "win_rate":
          aVal = a.win_rate;
          bVal = b.win_rate;
          break;
        case "avg_guesses":
          aVal = a.avg_guesses ?? 0;
          bVal = b.avg_guesses ?? 0;
          break;
        case "total_golf_score":
          aVal = a.total_golf_score;
          bVal = b.total_golf_score;
          break;
        case "recent_results": {
          const aWins = a.recent_results.filter(game => game.won).length;
          const bWins = b.recent_results.filter(game => game.won).length;
          aVal = aWins / Math.max(a.recent_results.length, 1);
          bVal = bWins / Math.max(b.recent_results.length, 1);
          break;
        }
        default:
          return 0;
      }

      if (aVal < bVal) return sortConfig.direction === "asc" ? -1 : 1;
      if (aVal > bVal) return sortConfig.direction === "asc" ? 1 : -1;
      return 0;
    });

    return sorted;
  }, [rawData, sortConfig]);

  const sortBy = (column: SortColumn) => {
    setSortConfig(prev => ({
      column,
      direction: prev.column === column && prev.direction === "desc" ? "asc" : "desc",
    }));
  };

  const refresh = () => {
    void fetchLeaderboard();
  };

  return {
    data: sortedData,
    metadata: rawData?.metadata ?? null,
    loading,
    error,
    sortConfig,
    sortBy,
    refresh,
  };
}
