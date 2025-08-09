// API Response Types

// Enums
export enum LetterStatus {
  CORRECT = "correct",
  PRESENT = "present",
  ABSENT = "absent",
}

export enum GameStatus {
  WON = "won",
  LOST = "lost",
}

// Single Game interface with optional relationships
export interface Game {
  // Core game data (always present)
  id: string;
  model_name: string;
  template_name: string;
  parser_name: string;
  target_word: string;
  date: string;
  status: GameStatus;
  guesses_count: number;
  won: boolean;
  duration_seconds: number;
  total_invalid_attempts: number;
  created_at: string;
  completed_at?: string;

  // Optional relationships (populated based on API parameters)
  turns?: GameTurn[];
  // Note: llm_interactions and invalid_attempts can be added when needed
}

export interface GameTurn {
  turn_number: number;
  guess: string;
  reasoning?: string;
  is_correct: boolean;
  letter_results: LetterResult[];
}

export interface LetterResult {
  position: number;
  letter: string;
  status: LetterStatus;
}

export interface LLMInteraction {
  id: string;
  turn_number: number;
  prompt: string;
  response: string;
  model_name: string;
  tokens_used?: number;
  response_time_ms?: number;
}

export interface InvalidWordAttempt {
  id: string;
  turn_number: number;
  attempted_word: string;
  reason: string;
}

// API Error Response
export interface ApiError {
  detail: string;
  status_code: number;
}
