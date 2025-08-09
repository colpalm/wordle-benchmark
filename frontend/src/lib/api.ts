import { Game, ApiError } from "@/types/api";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

class ApiClient {
  private async fetchJson<T>(endpoint: string): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      const error: ApiError = await response.json();
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
  }

  async getGamesByDate(date?: string, includeTurns: boolean = false): Promise<Game[]> {
    const params = new URLSearchParams();
    if (date) params.append("date_param", date);
    if (includeTurns) params.append("include_turns", "true");

    const queryString = params.toString() ? `?${params.toString()}` : "";
    return this.fetchJson<Game[]>(`/api/v1/games${queryString}`);
  }

  async healthCheck(): Promise<{ status: string }> {
    return this.fetchJson<{ status: string }>("/health");
  }
}

export const apiClient = new ApiClient();
