"""WebSocket handling for real-time game communication"""
import json
from typing import Dict, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import aiosqlite

from app.db.database import DATABASE_PATH
from app.services.story_manager import StoryManager

router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections per game"""
    
    def __init__(self):
        # game_id -> set of (player_id, websocket)
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, game_id: str, player_id: str):
        await websocket.accept()
        if game_id not in self.active_connections:
            self.active_connections[game_id] = {}
        self.active_connections[game_id][player_id] = websocket
        
        # Update player connection status
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute(
                "UPDATE players SET is_connected = 1 WHERE id = ? AND game_id = ?",
                (player_id, game_id)
            )
            await db.commit()
    
    async def disconnect(self, game_id: str, player_id: str):
        if game_id in self.active_connections:
            self.active_connections[game_id].pop(player_id, None)
            if not self.active_connections[game_id]:
                del self.active_connections[game_id]
        
        # Update player connection status
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute(
                "UPDATE players SET is_connected = 0 WHERE id = ? AND game_id = ?",
                (player_id, game_id)
            )
            await db.commit()
    
    async def broadcast(self, game_id: str, message: dict, exclude: str = None):
        """Send message to all players in a game"""
        if game_id not in self.active_connections:
            return
        
        message_json = json.dumps(message)
        for player_id, ws in self.active_connections[game_id].items():
            if player_id != exclude:
                try:
                    await ws.send_text(message_json)
                except:
                    pass
    
    async def send_to_player(self, game_id: str, player_id: str, message: dict):
        """Send message to a specific player"""
        if game_id in self.active_connections:
            ws = self.active_connections[game_id].get(player_id)
            if ws:
                try:
                    await ws.send_text(json.dumps(message))
                except:
                    pass


manager = ConnectionManager()


@router.websocket("/ws/games/{game_id}/{player_id}")
async def game_websocket(websocket: WebSocket, game_id: str, player_id: str):
    """WebSocket endpoint for game communication"""
    await manager.connect(websocket, game_id, player_id)
    
    # Get player name
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT name FROM players WHERE id = ? AND game_id = ?",
            (player_id, game_id)
        )
        player = await cursor.fetchone()
        player_name = player['name'] if player else "Unknown"
    
    # Notify others of join
    await manager.broadcast(game_id, {
        "type": "player_joined",
        "payload": {"player_id": player_id, "player_name": player_name}
    }, exclude=player_id)
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            await handle_message(game_id, player_id, player_name, message)
            
    except WebSocketDisconnect:
        await manager.disconnect(game_id, player_id)
        await manager.broadcast(game_id, {
            "type": "player_left",
            "payload": {"player_id": player_id, "player_name": player_name}
        })


async def handle_message(game_id: str, player_id: str, player_name: str, message: dict):
    """Handle incoming WebSocket messages"""
    msg_type = message.get("type")
    payload = message.get("payload", {})
    
    if msg_type == "chat":
        # Broadcast chat message
        content = payload.get("content", "")
        
        # Save to database
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute(
                "INSERT INTO messages (game_id, player_id, sender_name, content, message_type) VALUES (?, ?, ?, ?, ?)",
                (game_id, player_id, player_name, content, "chat")
            )
            await db.commit()
        
        await manager.broadcast(game_id, {
            "type": "chat",
            "payload": {
                "sender_id": player_id,
                "sender_name": player_name,
                "content": content
            }
        })
    
    elif msg_type == "search":
        # Player searching a location
        location_id = payload.get("location_id")
        item = payload.get("item")
        
        async with aiosqlite.connect(DATABASE_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT story_id FROM games WHERE id = ?", (game_id,)
            )
            game = await cursor.fetchone()
            
            if game:
                # Check for clues at this location
                clues = StoryManager.get_clues_at_location(game['story_id'], location_id)
                
                for clue in clues:
                    # Check if clue matches search item (if specified)
                    if item and item.lower() not in clue.get('discovery_hint', '').lower():
                        continue
                    
                    # Check if already found
                    cursor = await db.execute(
                        "SELECT id FROM found_clues WHERE game_id = ? AND clue_id = ?",
                        (game_id, clue['id'])
                    )
                    if await cursor.fetchone():
                        continue
                    
                    # Found a new clue!
                    await db.execute(
                        "INSERT INTO found_clues (game_id, clue_id, found_by) VALUES (?, ?, ?)",
                        (game_id, clue['id'], player_id)
                    )
                    await db.commit()
                    
                    # Broadcast the discovery
                    await manager.broadcast(game_id, {
                        "type": "clue_found",
                        "payload": {
                            "finder_id": player_id,
                            "finder_name": player_name,
                            "clue": {
                                "id": clue['id'],
                                "name": clue['name'],
                                "description": clue['description']
                            }
                        }
                    })
                    break
    
    elif msg_type == "phase_change":
        # Host changed game phase
        new_phase = payload.get("phase")
        await manager.broadcast(game_id, {
            "type": "phase_change",
            "payload": {"phase": new_phase}
        })
    
    elif msg_type == "vote":
        # Player cast a vote
        suspect_id = payload.get("suspect_id")
        
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute(
                "INSERT OR REPLACE INTO votes (game_id, voter_id, suspect_id) VALUES (?, ?, ?)",
                (game_id, player_id, suspect_id)
            )
            await db.commit()
        
        await manager.broadcast(game_id, {
            "type": "vote_cast",
            "payload": {
                "voter_id": player_id,
                "voter_name": player_name
            }
        })
