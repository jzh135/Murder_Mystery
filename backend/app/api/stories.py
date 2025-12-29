"""Stories API routes"""
from fastapi import APIRouter, HTTPException

from app.services.story_manager import StoryManager

router = APIRouter()


@router.get("")
async def list_stories():
    """Get all available stories"""
    return StoryManager.get_all_stories()


@router.get("/{story_id}")
async def get_story(story_id: str):
    """Get story details (without solution)"""
    story = StoryManager.get_story(story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    
    # Return story without revealing solution or private character info
    return {
        'id': story['id'],
        'title': story['title'],
        'title_cn': story.get('title_cn'),
        'description': story['description'],
        'player_count': story['player_count'],
        'difficulty': story['difficulty'],
        'duration_minutes': story['duration_minutes'],
        'setting': story.get('setting', {}),
        'victim': story.get('victim', {}),
        'locations': story.get('locations', []),
        'timeline': story.get('timeline', [])
    }


@router.get("/{story_id}/locations")
async def get_locations(story_id: str):
    """Get all locations in a story"""
    locations = StoryManager.get_locations(story_id)
    if not locations:
        raise HTTPException(status_code=404, detail="Story not found")
    return locations


@router.post("/reload")
async def reload_stories():
    """Reload all stories from disk"""
    StoryManager.reload_stories()
    stories = StoryManager.get_all_stories()
    return {"message": f"Reloaded {len(stories)} stories", "stories": stories}
