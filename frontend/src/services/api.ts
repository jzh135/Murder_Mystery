const API_BASE = '/api';

export async function fetchStories() {
  const res = await fetch(`${API_BASE}/stories`);
  if (!res.ok) throw new Error('Failed to fetch stories');
  return res.json();
}

export async function fetchStory(storyId: string) {
  const res = await fetch(`${API_BASE}/stories/${storyId}`);
  if (!res.ok) throw new Error('Failed to fetch story');
  return res.json();
}

export async function createGame(storyId: string, hostName: string) {
  const res = await fetch(`${API_BASE}/games`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ story_id: storyId, host_name: hostName }),
  });
  if (!res.ok) throw new Error('Failed to create game');
  return res.json();
}

export async function fetchGame(gameId: string) {
  const res = await fetch(`${API_BASE}/games/${gameId}`);
  if (!res.ok) throw new Error('Failed to fetch game');
  return res.json();
}

export async function joinGame(gameId: string, playerName: string) {
  const res = await fetch(`${API_BASE}/games/${gameId}/join`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ player_name: playerName }),
  });
  if (!res.ok) throw new Error('Failed to join game');
  return res.json();
}

export async function fetchCharacters(gameId: string) {
  const res = await fetch(`${API_BASE}/games/${gameId}/characters`);
  if (!res.ok) throw new Error('Failed to fetch characters');
  return res.json();
}

export async function selectCharacter(gameId: string, playerId: string, characterId: string) {
  const res = await fetch(`${API_BASE}/games/${gameId}/select-character`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ player_id: playerId, character_id: characterId }),
  });
  if (!res.ok) throw new Error('Failed to select character');
  return res.json();
}

export async function startGame(gameId: string, playerId: string) {
  const res = await fetch(`${API_BASE}/games/${gameId}/start?player_id=${playerId}`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error('Failed to start game');
  return res.json();
}

export async function advancePhase(gameId: string, playerId: string) {
  const res = await fetch(`${API_BASE}/games/${gameId}/phase?player_id=${playerId}`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error('Failed to advance phase');
  return res.json();
}

export async function getMyCharacter(gameId: string, playerId: string) {
  const res = await fetch(`${API_BASE}/games/${gameId}/my-character/${playerId}`);
  if (!res.ok) throw new Error('Failed to fetch character');
  return res.json();
}

export async function fetchLocations(storyId: string) {
  const res = await fetch(`${API_BASE}/stories/${storyId}/locations`);
  if (!res.ok) throw new Error('Failed to fetch locations');
  return res.json();
}
