"""Pydantic models for API requests and responses"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class GamePhase(str, Enum):
    LOBBY = "lobby"
    CHARACTER_SELECT = "character_select"
    SCRIPT_READING = "script_reading"
    INVESTIGATION = "investigation"
    DISCUSSION = "discussion"
    VOTING = "voting"
    REVEAL = "reveal"
    ENDED = "ended"


class GameStatus(str, Enum):
    WAITING = "waiting"
    IN_PROGRESS = "in_progress"
    FINISHED = "finished"


# Request models
class CreateGameRequest(BaseModel):
    story_id: str
    host_name: str


class JoinGameRequest(BaseModel):
    player_name: str


class SelectCharacterRequest(BaseModel):
    player_id: str
    character_id: str


class SendMessageRequest(BaseModel):
    player_id: str
    content: str


class SearchLocationRequest(BaseModel):
    player_id: str
    location_id: str
    item: Optional[str] = None


class CastVoteRequest(BaseModel):
    player_id: str
    suspect_character_id: str


# Response models
class PlayerInfo(BaseModel):
    id: str
    name: str
    character_id: Optional[str] = None
    character_name: Optional[str] = None
    is_host: bool = False
    is_connected: bool = True


class GameState(BaseModel):
    id: str
    story_id: str
    story_title: str
    status: GameStatus
    phase: GamePhase
    players: List[PlayerInfo]
    host_id: Optional[str] = None
    created_at: datetime


class ClueInfo(BaseModel):
    id: str
    name: str
    description: str
    location: str
    found_by: Optional[str] = None
    found_at: Optional[datetime] = None


class MessageInfo(BaseModel):
    id: int
    sender_name: str
    content: str
    message_type: str
    created_at: datetime


class CharacterPublicInfo(BaseModel):
    id: str
    name: str
    name_cn: Optional[str] = None
    public_info: str
    is_taken: bool = False


class CharacterPrivateInfo(BaseModel):
    id: str
    name: str
    name_cn: Optional[str] = None
    public_info: str
    private_background: str
    secrets: List[str]
    relationships: Dict[str, str]
    goals: List[str]


class StoryInfo(BaseModel):
    id: str
    title: str
    title_cn: Optional[str] = None
    description: str
    player_count: Dict[str, int]
    difficulty: str
    duration_minutes: int


class LocationInfo(BaseModel):
    id: str
    name: str
    name_cn: Optional[str] = None
    description: str
    searchable_items: List[str]


# WebSocket message models
class WSMessage(BaseModel):
    type: str
    payload: Dict[str, Any]
