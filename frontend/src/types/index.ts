// Game state types
export interface Player {
  id: string;
  name: string;
  character_id?: string;
  character_name?: string;
  is_host: boolean;
  is_connected: boolean;
}

export interface GameState {
  id: string;
  story_id: string;
  story_title: string;
  status: 'waiting' | 'in_progress' | 'finished';
  phase: GamePhase;
  players: Player[];
  host_id?: string;
  created_at: string;
}

export type GamePhase =
  | 'lobby'
  | 'character_select'
  | 'script_reading'
  | 'investigation'
  | 'discussion'
  | 'voting'
  | 'reveal'
  | 'ended';

// Story types
export interface Story {
  id: string;
  title: string;
  title_cn?: string;
  description: string;
  player_count: {
    min: number;
    max: number;
  };
  difficulty: string;
  duration_minutes: number;
}

export interface Character {
  id: string;
  name: string;
  name_cn?: string;
  public_info: string;
  is_taken?: boolean;
}

export interface CharacterPrivate extends Character {
  private_background: string;
  secrets: string[];
  relationships: Record<string, string>;
  goals: string[];
}

export interface Location {
  id: string;
  name: string;
  name_cn?: string;
  description: string;
  searchable_items: string[];
}

export interface Clue {
  id: string;
  name: string;
  description: string;
  location: string;
  found_by?: string;
  found_at?: string;
}

// WebSocket message types
export interface WSMessage {
  type: string;
  payload: Record<string, unknown>;
}

export interface ChatMessage {
  sender_id: string;
  sender_name: string;
  content: string;
  timestamp?: string;
}

export interface ClueFoundMessage {
  finder_id: string;
  finder_name: string;
  clue: {
    id: string;
    name: string;
    description: string;
  };
}

// API response types
export interface CreateGameResponse {
  game_id: string;
  player_id: string;
  message: string;
}

export interface JoinGameResponse {
  player_id: string;
  game_id: string;
  message: string;
}
