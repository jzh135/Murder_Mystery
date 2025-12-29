"""LangGraph Game Master Agent

The AI Game Master that manages the narrative flow of the murder mystery game.
Uses Gemini 2.0 Flash to generate dynamic responses based on game state.
"""
import os
from typing import TypedDict, List, Optional, Annotated
from operator import add

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END

from app.services.story_manager import StoryManager


class GameMasterState(TypedDict):
    """State for the Game Master agent"""
    game_id: str
    story_id: str
    phase: str
    players: List[dict]  # List of {id, name, character_id}
    found_clues: List[str]  # List of clue IDs
    messages: Annotated[List[dict], add]  # Chat history
    current_action: Optional[str]
    response: Optional[str]


def get_llm():
    """Get the Gemini model"""
    return ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-exp",
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0.7
    )


def build_game_context(state: GameMasterState) -> str:
    """Build context string for the LLM"""
    story = StoryManager.get_story(state['story_id'])
    if not story:
        return "Unknown story"
    
    # Build player info
    player_info = []
    for p in state['players']:
        char = StoryManager.get_character_private(state['story_id'], p.get('character_id', ''))
        if char:
            player_info.append(f"- {p['name']} plays {char['name']}")
    
    # Build clue info
    found_clue_info = []
    for clue_id in state['found_clues']:
        clue = StoryManager.get_clue(state['story_id'], clue_id)
        if clue:
            found_clue_info.append(f"- {clue['name']}: {clue['description']}")
    
    context = f"""
STORY: {story['title']}
SETTING: {story.get('setting', {}).get('location', 'Unknown')} - {story.get('setting', {}).get('atmosphere', '')}
VICTIM: {story.get('victim', {}).get('name', 'Unknown')} - {story.get('victim', {}).get('description', '')}

CURRENT PHASE: {state['phase']}

PLAYERS:
{chr(10).join(player_info) if player_info else 'No players yet'}

CLUES DISCOVERED:
{chr(10).join(found_clue_info) if found_clue_info else 'No clues found yet'}
"""
    return context


def create_system_prompt(phase: str, story: dict) -> str:
    """Create system prompt based on game phase"""
    base_prompt = """You are the Game Master (主持人) for a murder mystery game (剧本杀). 
Your role is to guide players through the mystery, reveal information appropriately, 
and create an immersive, suspenseful atmosphere.

RULES:
- Never reveal the solution or who the culprit is until the reveal phase
- Be dramatic and atmospheric in your narration
- Respond in the same language the player uses
- Keep responses concise but engaging (2-4 paragraphs max)
- Use Chinese (中文) if players speak Chinese
"""

    phase_prompts = {
        "script_reading": """
CURRENT TASK: Introduction Phase (阅读剧本)
- Dramatically introduce the setting and victim
- Set the scene for the mystery
- Build tension and atmosphere
""",
        "investigation": """
CURRENT TASK: Investigation Phase (搜证阶段)
- Guide players in their search
- Give hints about where to look without revealing too much
- React to clue discoveries with appropriate dramatic flair
- Encourage players to discuss findings
""",
        "discussion": """
CURRENT TASK: Discussion Phase (集中讨论)
- Facilitate discussion between players
- Ask probing questions to spark debate
- Summarize key points when helpful
- Build tension as the vote approaches
""",
        "voting": """
CURRENT TASK: Voting Phase (投票阶段)
- Remind players of the gravity of their decision
- Create dramatic tension
- Do NOT reveal any hints about the true culprit
""",
        "reveal": f"""
CURRENT TASK: Truth Reveal Phase (真相揭晓)
- Dramatically reveal what really happened
- The solution is: {story.get('solution', {}).get('full_explanation', 'Unknown')}
- Build up the reveal with tension
- Congratulate correct guesses or console wrong ones
"""
    }
    
    return base_prompt + phase_prompts.get(phase, "")


def introduce_scene(state: GameMasterState) -> dict:
    """Generate the opening narration"""
    story = StoryManager.get_story(state['story_id'])
    if not story:
        return {"response": "Story not found."}
    
    llm = get_llm()
    
    intro = story.get('phases', {}).get('intro_narration', '')
    context = build_game_context(state)
    
    prompt = f"""
{create_system_prompt('script_reading', story)}

CONTEXT:
{context}

PREPARED INTRODUCTION:
{intro}

Now, as the Game Master, deliver a dramatic opening narration based on the above. 
Expand on the prepared introduction with atmospheric details.
Make players feel the tension and mystery.
"""
    
    response = llm.invoke(prompt)
    return {"response": response.content}


def guide_investigation(state: GameMasterState) -> dict:
    """Guide players during investigation"""
    story = StoryManager.get_story(state['story_id'])
    if not story:
        return {"response": "Story not found."}
    
    llm = get_llm()
    context = build_game_context(state)
    action = state.get('current_action', '')
    
    # Get unfound clues to subtly hint at
    all_clues = story.get('clues', [])
    unfound = [c for c in all_clues if c['id'] not in state['found_clues']]
    
    prompt = f"""
{create_system_prompt('investigation', story)}

CONTEXT:
{context}

PLAYER ACTION: {action}

UNFOUND CLUES (for your reference, do NOT reveal directly):
{[c['name'] + ' at ' + c['location'] for c in unfound]}

Respond to the player's action or question. If they're stuck, give subtle hints.
"""
    
    response = llm.invoke(prompt)
    return {"response": response.content}


def facilitate_discussion(state: GameMasterState) -> dict:
    """Facilitate the discussion phase"""
    story = StoryManager.get_story(state['story_id'])
    if not story:
        return {"response": "Story not found."}
    
    llm = get_llm()
    context = build_game_context(state)
    
    discussion_prompts = story.get('phases', {}).get('discussion_prompts', [])
    
    prompt = f"""
{create_system_prompt('discussion', story)}

CONTEXT:
{context}

RECENT MESSAGES:
{state.get('messages', [])[-5:]}

SUGGESTED DISCUSSION QUESTIONS:
{discussion_prompts}

Facilitate the discussion. Ask a probing question or summarize a key point.
Build tension toward the upcoming vote.
"""
    
    response = llm.invoke(prompt)
    return {"response": response.content}


def announce_voting(state: GameMasterState) -> dict:
    """Announce voting phase"""
    story = StoryManager.get_story(state['story_id'])
    if not story:
        return {"response": "Story not found."}
    
    llm = get_llm()
    context = build_game_context(state)
    
    prompt = f"""
{create_system_prompt('voting', story)}

CONTEXT:
{context}

Dramatically announce that voting is about to begin.
Remind players of what's at stake.
Do NOT give any hints about who the culprit is.
"""
    
    response = llm.invoke(prompt)
    return {"response": response.content}


def reveal_truth(state: GameMasterState) -> dict:
    """Reveal the solution"""
    story = StoryManager.get_story(state['story_id'])
    if not story:
        return {"response": "Story not found."}
    
    llm = get_llm()
    context = build_game_context(state)
    solution = story.get('solution', {})
    
    prompt = f"""
{create_system_prompt('reveal', story)}

CONTEXT:
{context}

SOLUTION DETAILS:
- Culprit: {solution.get('culprit_id')}
- Method: {solution.get('method')}
- Motive: {solution.get('motive')}
- Full Story: {solution.get('full_explanation')}

Dramatically reveal what really happened. Build suspense before the big reveal.
Describe the culprit's actions step by step.
"""
    
    response = llm.invoke(prompt)
    return {"response": response.content}


def route_by_phase(state: GameMasterState) -> str:
    """Route to appropriate node based on game phase"""
    phase = state.get('phase', 'script_reading')
    
    if phase == 'script_reading':
        return 'introduce'
    elif phase == 'investigation':
        return 'investigate'
    elif phase == 'discussion':
        return 'discuss'
    elif phase == 'voting':
        return 'voting'
    elif phase == 'reveal':
        return 'reveal'
    else:
        return END


def build_game_master_graph():
    """Build the LangGraph workflow for the Game Master"""
    workflow = StateGraph(GameMasterState)
    
    # Add nodes
    workflow.add_node("introduce", introduce_scene)
    workflow.add_node("investigate", guide_investigation)
    workflow.add_node("discuss", facilitate_discussion)
    workflow.add_node("voting", announce_voting)
    workflow.add_node("reveal", reveal_truth)
    
    # Set entry point with conditional routing
    workflow.set_conditional_entry_point(route_by_phase)
    
    # All nodes end after execution
    workflow.add_edge("introduce", END)
    workflow.add_edge("investigate", END)
    workflow.add_edge("discuss", END)
    workflow.add_edge("voting", END)
    workflow.add_edge("reveal", END)
    
    return workflow.compile()


# Compiled graph instance
game_master = build_game_master_graph()


async def get_game_master_response(
    game_id: str,
    story_id: str,
    phase: str,
    players: List[dict],
    found_clues: List[str],
    messages: List[dict] = None,
    current_action: str = None
) -> str:
    """Get a response from the Game Master agent"""
    state: GameMasterState = {
        "game_id": game_id,
        "story_id": story_id,
        "phase": phase,
        "players": players,
        "found_clues": found_clues,
        "messages": messages or [],
        "current_action": current_action,
        "response": None
    }
    
    result = game_master.invoke(state)
    return result.get("response", "The Game Master is silent...")
