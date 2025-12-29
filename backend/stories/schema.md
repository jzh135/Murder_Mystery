# Story JSON Schema

Stories are defined in JSON format. Place files in the `backend/stories/` directory.

## Schema

```json
{
  "id": "unique-story-id",
  "title": "Story Title",
  "title_cn": "中文标题",
  "description": "Brief story description",
  "player_count": {
    "min": 4,
    "max": 6
  },
  "difficulty": "medium",
  "duration_minutes": 90,
  "setting": {
    "time": "1920s",
    "location": "Art Deco Mansion",
    "atmosphere": "Mysterious, elegant, tense"
  },
  "characters": [
    {
      "id": "char-001",
      "name": "Character Name",
      "name_cn": "角色名",
      "role": "suspect",
      "is_culprit": false,
      "public_info": "What everyone knows about this character",
      "private_background": "Secret background only this player sees",
      "secrets": ["Secret 1", "Secret 2"],
      "relationships": {
        "char-002": "rival",
        "char-003": "friend"
      },
      "goals": ["Find out who stole the painting", "Protect your alibi"]
    }
  ],
  "victim": {
    "name": "Victim Name",
    "description": "Who the victim was"
  },
  "clues": [
    {
      "id": "clue-001",
      "name": "Torn Letter",
      "description": "A partially burned letter with threatening words",
      "location": "library",
      "discovery_hint": "Check the fireplace",
      "reveals": "char-002 had a motive",
      "required": true
    }
  ],
  "locations": [
    {
      "id": "library",
      "name": "The Library",
      "name_cn": "图书馆",
      "description": "A grand room filled with antique books",
      "searchable_items": ["fireplace", "desk", "bookshelf"]
    }
  ],
  "timeline": [
    {
      "time": "8:00 PM",
      "event": "Dinner begins"
    },
    {
      "time": "9:30 PM",
      "event": "Victim found dead"
    }
  ],
  "solution": {
    "culprit_id": "char-003",
    "method": "Poison in the wine",
    "motive": "Revenge for past betrayal",
    "full_explanation": "Detailed explanation of what happened..."
  },
  "phases": {
    "intro_narration": "The night was dark and stormy...",
    "investigation_prompts": [
      "Where were you at 9 PM?",
      "Did you hear anything unusual?"
    ],
    "discussion_prompts": [
      "Who had access to the wine cellar?",
      "What was the victim's relationship with everyone?"
    ]
  }
}
```

## Fields Reference

| Field | Required | Description |
|-------|----------|-------------|
| `id` | Yes | Unique identifier for the story |
| `title` | Yes | English title |
| `title_cn` | No | Chinese title |
| `player_count` | Yes | Min/max players |
| `characters` | Yes | Array of playable characters |
| `clues` | Yes | Array of discoverable clues |
| `locations` | Yes | Searchable locations |
| `solution` | Yes | The truth behind the mystery |

## Character Roles

- `suspect` - Could be the culprit
- `witness` - Saw something important
- `detective` - Investigating the case (optional role)

## Tips for Creating Stories

1. Every character should have secrets, even innocents
2. Create red herrings to mislead players
3. Required clues should be findable through normal gameplay
4. Balance the information - no one should know too much
