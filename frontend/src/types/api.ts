// API Response Types

// Enums
export enum LetterStatus {
  CORRECT = 'correct',
  PRESENT = 'present',
  ABSENT = 'absent'
}

export enum GameStatus {
  WON = 'won',
  LOST = 'lost'
}

// Basic game info from list endpoint
export interface GameSummary {
  id: string;
  model_name: string;
  target_word: string;
  date: string;
  status: GameStatus;
  guesses_count: number;
  won: boolean;
  duration_seconds: number;
}

// Full game details from individual game endpoint
export interface GameDetails extends GameSummary {
  turns: GameTurn[];
  llm_interactions?: LLMInteraction[];
  invalid_attempts?: InvalidWordAttempt[];
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