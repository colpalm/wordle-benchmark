export interface LeaderboardEntry {
  model_name: string;
  total_games: number;
  wins: number;
  win_rate: number;
  avg_guesses: number | null;
  total_golf_score: number;
  recent_results: GameResult[];
}

export interface GameResult {
  date: string;
  won: boolean;
}

export interface LeaderboardResponse {
  leaderboard: LeaderboardEntry[];
  metadata: {
    total_games: number;
    total_models: number;
    last_updated: string;
  };
}

export type SortColumn = "model_name" | "win_rate" | "avg_guesses" | "total_golf_score" | "recent_results";
export type SortDirection = "asc" | "desc";

export interface SortConfig {
  column: SortColumn;
  direction: SortDirection;
}
