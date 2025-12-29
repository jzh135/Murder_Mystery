"""Games API routes"""
import uuid
from fastapi import APIRouter, HTTPException, Depends
import aiosqlite

from app.db.database import get_db
from app.models.schemas import (
    CreateGameRequest, JoinGameRequest, SelectCharacterRequest,
    GameState, GamePhase, GameStatus, PlayerInfo
)
from app.services.story_manager import StoryManager

router = APIRouter()


@router.post("", response_model=dict)
async def create_game(request: CreateGameRequest, db: aiosqlite.Connection = Depends(get_db)):
    """Create a new game session"""
    # Verify story exists
    story = StoryManager.get_story(request.story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    
    game_id = str(uuid.uuid4())[:8]  # Short ID for easy sharing
    player_id = str(uuid.uuid4())
    
    # Create game
    await db.execute(
        "INSERT INTO games (id, story_id, host_id, status, current_phase) VALUES (?, ?, ?, ?, ?)",
        (game_id, request.story_id, player_id, GameStatus.WAITING, GamePhase.LOBBY)
    )
    
    # Add host as first player
    await db.execute(
        "INSERT INTO players (id, game_id, name, is_host) VALUES (?, ?, ?, ?)",
        (player_id, game_id, request.host_name, 1)
    )
    
    await db.commit()
    
    return {
        "game_id": game_id,
        "player_id": player_id,
        "message": f"Game created! Share code: {game_id}"
    }


@router.get("/{game_id}", response_model=GameState)
async def get_game(game_id: str, db: aiosqlite.Connection = Depends(get_db)):
    """Get current game state"""
    cursor = await db.execute(
        "SELECT * FROM games WHERE id = ?", (game_id,)
    )
    game = await cursor.fetchone()
    
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    # Get players
    cursor = await db.execute(
        "SELECT * FROM players WHERE game_id = ?", (game_id,)
    )
    players_rows = await cursor.fetchall()
    
    story = StoryManager.get_story(game['story_id'])
    
    players = []
    for p in players_rows:
        char_name = None
        if p['character_id']:
            char = StoryManager.get_character_private(game['story_id'], p['character_id'])
            char_name = char['name'] if char else None
        
        players.append(PlayerInfo(
            id=p['id'],
            name=p['name'],
            character_id=p['character_id'],
            character_name=char_name,
            is_host=bool(p['is_host']),
            is_connected=bool(p['is_connected'])
        ))
    
    return GameState(
        id=game['id'],
        story_id=game['story_id'],
        story_title=story['title'] if story else "Unknown",
        status=game['status'],
        phase=game['current_phase'],
        players=players,
        host_id=game['host_id'],
        created_at=game['created_at']
    )


@router.post("/{game_id}/join", response_model=dict)
async def join_game(game_id: str, request: JoinGameRequest, db: aiosqlite.Connection = Depends(get_db)):
    """Join an existing game"""
    cursor = await db.execute(
        "SELECT * FROM games WHERE id = ?", (game_id,)
    )
    game = await cursor.fetchone()
    
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    if game['status'] != GameStatus.WAITING:
        raise HTTPException(status_code=400, detail="Game already in progress")
    
    # Check player count
    story = StoryManager.get_story(game['story_id'])
    cursor = await db.execute(
        "SELECT COUNT(*) as count FROM players WHERE game_id = ?", (game_id,)
    )
    count = await cursor.fetchone()
    
    if count['count'] >= story['player_count']['max']:
        raise HTTPException(status_code=400, detail="Game is full")
    
    player_id = str(uuid.uuid4())
    
    await db.execute(
        "INSERT INTO players (id, game_id, name) VALUES (?, ?, ?)",
        (player_id, game_id, request.player_name)
    )
    await db.commit()
    
    return {
        "player_id": player_id,
        "game_id": game_id,
        "message": f"Joined game as {request.player_name}"
    }


@router.get("/{game_id}/characters")
async def get_available_characters(game_id: str, db: aiosqlite.Connection = Depends(get_db)):
    """Get available characters for selection"""
    cursor = await db.execute(
        "SELECT story_id FROM games WHERE id = ?", (game_id,)
    )
    game = await cursor.fetchone()
    
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    # Get all characters
    characters = StoryManager.get_characters(game['story_id'])
    
    # Get taken characters
    cursor = await db.execute(
        "SELECT character_id FROM players WHERE game_id = ? AND character_id IS NOT NULL",
        (game_id,)
    )
    taken = await cursor.fetchall()
    taken_ids = {row['character_id'] for row in taken}
    
    # Mark taken characters
    for char in characters:
        char['is_taken'] = char['id'] in taken_ids
    
    return characters


@router.post("/{game_id}/select-character")
async def select_character(
    game_id: str, 
    request: SelectCharacterRequest, 
    db: aiosqlite.Connection = Depends(get_db)
):
    """Select a character for a player"""
    # Verify game exists
    cursor = await db.execute(
        "SELECT * FROM games WHERE id = ?", (game_id,)
    )
    game = await cursor.fetchone()
    
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    # Verify character exists
    char = StoryManager.get_character_private(game['story_id'], request.character_id)
    if not char:
        raise HTTPException(status_code=404, detail="Character not found")
    
    # Check if character is already taken
    cursor = await db.execute(
        "SELECT id FROM players WHERE game_id = ? AND character_id = ?",
        (game_id, request.character_id)
    )
    if await cursor.fetchone():
        raise HTTPException(status_code=400, detail="Character already taken")
    
    # Update player's character
    await db.execute(
        "UPDATE players SET character_id = ? WHERE id = ? AND game_id = ?",
        (request.character_id, request.player_id, game_id)
    )
    await db.commit()
    
    return {"message": f"Selected character: {char['name']}"}


@router.post("/{game_id}/start")
async def start_game(game_id: str, player_id: str, db: aiosqlite.Connection = Depends(get_db)):
    """Start the game (host only)"""
    cursor = await db.execute(
        "SELECT * FROM games WHERE id = ?", (game_id,)
    )
    game = await cursor.fetchone()
    
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    if game['host_id'] != player_id:
        raise HTTPException(status_code=403, detail="Only host can start the game")
    
    # Check all players have characters
    cursor = await db.execute(
        "SELECT COUNT(*) as total, SUM(CASE WHEN character_id IS NOT NULL THEN 1 ELSE 0 END) as ready FROM players WHERE game_id = ?",
        (game_id,)
    )
    counts = await cursor.fetchone()
    
    story = StoryManager.get_story(game['story_id'])
    if counts['total'] < story['player_count']['min']:
        raise HTTPException(
            status_code=400, 
            detail=f"Need at least {story['player_count']['min']} players"
        )
    
    if counts['total'] != counts['ready']:
        raise HTTPException(status_code=400, detail="All players must select characters")
    
    # Start game
    await db.execute(
        "UPDATE games SET status = ?, current_phase = ? WHERE id = ?",
        (GameStatus.IN_PROGRESS, GamePhase.SCRIPT_READING, game_id)
    )
    await db.commit()
    
    return {"message": "Game started!", "phase": GamePhase.SCRIPT_READING}


@router.post("/{game_id}/phase")
async def advance_phase(
    game_id: str, 
    player_id: str, 
    db: aiosqlite.Connection = Depends(get_db)
):
    """Advance to the next game phase (host only)"""
    cursor = await db.execute(
        "SELECT * FROM games WHERE id = ?", (game_id,)
    )
    game = await cursor.fetchone()
    
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    if game['host_id'] != player_id:
        raise HTTPException(status_code=403, detail="Only host can advance phase")
    
    # Define phase progression
    phase_order = [
        GamePhase.LOBBY,
        GamePhase.CHARACTER_SELECT,
        GamePhase.SCRIPT_READING,
        GamePhase.INVESTIGATION,
        GamePhase.DISCUSSION,
        GamePhase.VOTING,
        GamePhase.REVEAL,
        GamePhase.ENDED
    ]
    
    current_idx = phase_order.index(game['current_phase'])
    if current_idx >= len(phase_order) - 1:
        raise HTTPException(status_code=400, detail="Game already ended")
    
    next_phase = phase_order[current_idx + 1]
    
    await db.execute(
        "UPDATE games SET current_phase = ? WHERE id = ?",
        (next_phase, game_id)
    )
    await db.commit()
    
    return {"message": f"Advanced to {next_phase}", "phase": next_phase}


@router.get("/{game_id}/my-character/{player_id}")
async def get_my_character(
    game_id: str, 
    player_id: str, 
    db: aiosqlite.Connection = Depends(get_db)
):
    """Get the player's character with private info"""
    cursor = await db.execute(
        "SELECT p.character_id, g.story_id FROM players p JOIN games g ON p.game_id = g.id WHERE p.id = ? AND p.game_id = ?",
        (player_id, game_id)
    )
    result = await cursor.fetchone()
    
    if not result:
        raise HTTPException(status_code=404, detail="Player not found in game")
    
    if not result['character_id']:
        raise HTTPException(status_code=400, detail="No character selected")
    
    char = StoryManager.get_character_private(result['story_id'], result['character_id'])
    if not char:
        raise HTTPException(status_code=404, detail="Character not found")
    
    return char
