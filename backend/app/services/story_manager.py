"""Story loading and management"""
import json
from pathlib import Path
from typing import Dict, List, Optional, Any

STORIES_DIR = Path(__file__).parent.parent.parent / "stories"


class StoryManager:
    _stories: Dict[str, dict] = {}
    _loaded: bool = False
    
    @classmethod
    def load_stories(cls) -> None:
        """Load all story JSON files from the stories directory"""
        cls._stories = {}
        
        if not STORIES_DIR.exists():
            print(f"Stories directory not found: {STORIES_DIR}")
            return
        
        for story_file in STORIES_DIR.glob("*.json"):
            try:
                with open(story_file, 'r', encoding='utf-8') as f:
                    story = json.load(f)
                    cls._stories[story['id']] = story
                    print(f"Loaded story: {story['title']}")
            except Exception as e:
                print(f"Error loading story {story_file}: {e}")
        
        cls._loaded = True
        print(f"Loaded {len(cls._stories)} stories")
    
    @classmethod
    def get_all_stories(cls) -> List[dict]:
        """Get list of all available stories (summary info only)"""
        if not cls._loaded:
            cls.load_stories()
        
        return [
            {
                'id': story['id'],
                'title': story['title'],
                'title_cn': story.get('title_cn'),
                'description': story['description'],
                'player_count': story['player_count'],
                'difficulty': story['difficulty'],
                'duration_minutes': story['duration_minutes']
            }
            for story in cls._stories.values()
        ]
    
    @classmethod
    def get_story(cls, story_id: str) -> Optional[dict]:
        """Get full story by ID"""
        if not cls._loaded:
            cls.load_stories()
        return cls._stories.get(story_id)
    
    @classmethod
    def get_characters(cls, story_id: str) -> List[dict]:
        """Get characters for a story (public info only)"""
        story = cls.get_story(story_id)
        if not story:
            return []
        
        return [
            {
                'id': char['id'],
                'name': char['name'],
                'name_cn': char.get('name_cn'),
                'public_info': char['public_info']
            }
            for char in story.get('characters', [])
        ]
    
    @classmethod
    def get_character_private(cls, story_id: str, character_id: str) -> Optional[dict]:
        """Get full character info including private details"""
        story = cls.get_story(story_id)
        if not story:
            return None
        
        for char in story.get('characters', []):
            if char['id'] == character_id:
                return char
        return None
    
    @classmethod
    def get_locations(cls, story_id: str) -> List[dict]:
        """Get all locations in a story"""
        story = cls.get_story(story_id)
        if not story:
            return []
        return story.get('locations', [])
    
    @classmethod
    def get_clue(cls, story_id: str, clue_id: str) -> Optional[dict]:
        """Get a specific clue by ID"""
        story = cls.get_story(story_id)
        if not story:
            return None
        
        for clue in story.get('clues', []):
            if clue['id'] == clue_id:
                return clue
        return None
    
    @classmethod
    def get_clues_at_location(cls, story_id: str, location_id: str) -> List[dict]:
        """Get all clues at a specific location"""
        story = cls.get_story(story_id)
        if not story:
            return []
        
        return [
            clue for clue in story.get('clues', [])
            if clue['location'] == location_id
        ]
    
    @classmethod
    def get_solution(cls, story_id: str) -> Optional[dict]:
        """Get the story solution"""
        story = cls.get_story(story_id)
        if not story:
            return None
        return story.get('solution')
    
    @classmethod
    def get_intro_narration(cls, story_id: str) -> str:
        """Get the introduction narration"""
        story = cls.get_story(story_id)
        if not story:
            return ""
        return story.get('phases', {}).get('intro_narration', '')
    
    @classmethod
    def reload_stories(cls) -> None:
        """Force reload all stories"""
        cls._loaded = False
        cls.load_stories()
