import { useState, useEffect, useCallback, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { fetchGame, getMyCharacter, fetchLocations, advancePhase } from '../services/api';
import { useWebSocket } from '../hooks/useWebSocket';
import type { GameState, CharacterPrivate, Location, Clue, ChatMessage, WSMessage } from '../types';

const PHASE_LABELS: Record<string, string> = {
  script_reading: '📜 Script Reading | 阅读剧本',
  investigation: '🔍 Investigation | 搜证阶段',
  discussion: '💬 Discussion | 集中讨论',
  voting: '🗳️ Voting | 投票阶段',
  reveal: '🎭 Truth Reveal | 真相揭晓',
  ended: '🏁 Game Over',
};

export default function Game() {
  const { gameId } = useParams<{ gameId: string }>();
  const playerId = sessionStorage.getItem('playerId');
  const playerName = sessionStorage.getItem('playerName');

  const [game, setGame] = useState<GameState | null>(null);
  const [character, setCharacter] = useState<CharacterPrivate | null>(null);
  const [locations, setLocations] = useState<Location[]>([]);
  const [clues, setClues] = useState<Clue[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [selectedLocation, setSelectedLocation] = useState<string | null>(null);
  const [showScript, setShowScript] = useState(true);

  const chatEndRef = useRef<HTMLDivElement>(null);
  const { isConnected, sendMessage, addMessageHandler } = useWebSocket(gameId || null, playerId);

  const loadData = useCallback(async () => {
    if (!gameId || !playerId) return;
    try {
      const gameData = await fetchGame(gameId);
      setGame(gameData);

      const charData = await getMyCharacter(gameId, playerId);
      setCharacter(charData);

      const locData = await fetchLocations(gameData.story_id);
      setLocations(locData);
    } catch (e) {
      console.error('Failed to load game data:', e);
    }
  }, [gameId, playerId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  useEffect(() => {
    const cleanup = addMessageHandler((message: WSMessage) => {
      if (message.type === 'chat') {
        const payload = message.payload as unknown as ChatMessage;
        setMessages(prev => [...prev, payload]);
      } else if (message.type === 'clue_found') {
        const payload = message.payload as { finder_name: string; clue: Clue };
        setClues(prev => [...prev, payload.clue]);
        // Add system message
        setMessages(prev => [...prev, {
          sender_id: 'system',
          sender_name: '🔍 System',
          content: `${payload.finder_name} found: ${payload.clue.name}`,
        }]);
      } else if (message.type === 'phase_change') {
        loadData(); // Refresh game state
      } else if (message.type === 'player_joined' || message.type === 'player_left') {
        loadData();
      }
    });
    return () => { cleanup(); };
  }, [addMessageHandler, loadData]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendChat = () => {
    if (!chatInput.trim()) return;
    sendMessage('chat', { content: chatInput.trim() });
    setChatInput('');
  };

  const handleSearch = (locationId: string, item?: string) => {
    sendMessage('search', { location_id: locationId, item });
    setMessages(prev => [...prev, {
      sender_id: 'system',
      sender_name: '🔍 System',
      content: `${playerName} is searching ${item || 'the area'}...`,
    }]);
  };

  const handleAdvancePhase = async () => {
    if (!gameId || !playerId) return;
    try {
      await advancePhase(gameId, playerId);
      sendMessage('phase_change', { phase: 'next' });
      loadData();
    } catch (e) {
      console.error('Failed to advance phase:', e);
    }
  };

  const isHost = game?.host_id === playerId;

  if (!game || !character) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-xl text-zinc-400 animate-pulse-subtle">Loading game...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col">
      {/* Top bar */}
      <div className="bg-zinc-900/80 backdrop-blur border-b border-zinc-800 p-4">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <div>
            <h1 className="text-xl font-bold">{game.story_title}</h1>
            <p className="text-amber-400 text-sm">{PHASE_LABELS[game.phase] || game.phase}</p>
          </div>
          <div className="flex items-center gap-4">
            <span className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
            <span className="text-zinc-400">Playing as</span>
            <span className="font-semibold text-amber-400">{character.name}</span>
            {isHost && (
              <button onClick={handleAdvancePhase} className="btn-secondary text-sm py-2 px-4">
                Next Phase →
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left panel - Character Info & Clues */}
        <div className="w-80 bg-zinc-900/50 border-r border-zinc-800 flex flex-col overflow-hidden">
          {/* Character tabs */}
          <div className="flex border-b border-zinc-800">
            <button
              onClick={() => setShowScript(true)}
              className={`flex-1 py-3 text-sm font-medium ${showScript ? 'text-amber-400 border-b-2 border-amber-400' : 'text-zinc-500'}`}
            >
              My Script
            </button>
            <button
              onClick={() => setShowScript(false)}
              className={`flex-1 py-3 text-sm font-medium ${!showScript ? 'text-amber-400 border-b-2 border-amber-400' : 'text-zinc-500'}`}
            >
              Clues ({clues.length})
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-4">
            {showScript ? (
              <div className="space-y-4 animate-fade-in">
                <div>
                  <h3 className="text-lg font-semibold text-amber-400 mb-2">
                    {character.name} {character.name_cn && `(${character.name_cn})`}
                  </h3>
                  <p className="text-sm text-zinc-300">{character.private_background}</p>
                </div>

                <div>
                  <h4 className="font-medium text-red-400 mb-2">🤫 Your Secrets</h4>
                  <ul className="text-sm text-zinc-300 space-y-2">
                    {character.secrets.map((secret, i) => (
                      <li key={i} className="p-2 bg-red-900/20 rounded border border-red-900/30">
                        {secret}
                      </li>
                    ))}
                  </ul>
                </div>

                <div>
                  <h4 className="font-medium text-purple-400 mb-2">👥 Relationships</h4>
                  <ul className="text-sm text-zinc-300 space-y-1">
                    {Object.entries(character.relationships).map(([id, relation]) => (
                      <li key={id} className="flex justify-between">
                        <span className="capitalize">{id}</span>
                        <span className="text-zinc-500">{relation}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                <div>
                  <h4 className="font-medium text-green-400 mb-2">🎯 Your Goals</h4>
                  <ul className="text-sm text-zinc-300 space-y-1 list-disc list-inside">
                    {character.goals.map((goal, i) => (
                      <li key={i}>{goal}</li>
                    ))}
                  </ul>
                </div>
              </div>
            ) : (
              <div className="space-y-3 animate-fade-in">
                {clues.length === 0 ? (
                  <p className="text-zinc-500 text-sm">No clues found yet. Search locations to find clues!</p>
                ) : (
                  clues.map((clue) => (
                    <div key={clue.id} className="p-3 bg-amber-900/20 rounded-lg border border-amber-900/30">
                      <h4 className="font-medium text-amber-400">{clue.name}</h4>
                      <p className="text-sm text-zinc-300 mt-1">{clue.description}</p>
                    </div>
                  ))
                )}
              </div>
            )}
          </div>
        </div>

        {/* Center - Chat */}
        <div className="flex-1 flex flex-col">
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {messages.map((msg, i) => (
              <div
                key={i}
                className={`animate-fade-in ${msg.sender_id === 'system'
                  ? 'text-center'
                  : msg.sender_id === playerId
                    ? 'flex justify-end'
                    : 'flex justify-start'
                  }`}
              >
                {msg.sender_id === 'system' ? (
                  <span className="text-sm text-amber-400/70 italic">{msg.content}</span>
                ) : (
                  <div
                    className={`max-w-[70%] p-3 rounded-lg ${msg.sender_id === playerId
                      ? 'bg-amber-900/40 border border-amber-700/30'
                      : 'bg-zinc-800/60 border border-zinc-700/30'
                      }`}
                  >
                    <p className="text-xs text-zinc-400 mb-1">{msg.sender_name}</p>
                    <p className="text-sm">{msg.content}</p>
                  </div>
                )}
              </div>
            ))}
            <div ref={chatEndRef} />
          </div>

          {/* Chat input */}
          <div className="p-4 border-t border-zinc-800">
            <div className="flex gap-2">
              <input
                type="text"
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSendChat()}
                placeholder="Type a message..."
                className="input-dark flex-1"
              />
              <button onClick={handleSendChat} className="btn-primary">
                Send
              </button>
            </div>
          </div>
        </div>

        {/* Right panel - Locations */}
        {game.phase === 'investigation' && (
          <div className="w-72 bg-zinc-900/50 border-l border-zinc-800 flex flex-col overflow-hidden">
            <div className="p-4 border-b border-zinc-800">
              <h3 className="font-semibold">📍 Locations</h3>
            </div>
            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              {locations.map((loc) => (
                <div key={loc.id} className="glass-card p-3">
                  <button
                    onClick={() => setSelectedLocation(selectedLocation === loc.id ? null : loc.id)}
                    className="w-full text-left"
                  >
                    <h4 className="font-medium">
                      {loc.name} {loc.name_cn && <span className="text-zinc-400">({loc.name_cn})</span>}
                    </h4>
                    <p className="text-xs text-zinc-500 mt-1">{loc.description}</p>
                  </button>

                  {selectedLocation === loc.id && (
                    <div className="mt-3 pt-3 border-t border-zinc-700 space-y-2">
                      <p className="text-xs text-zinc-400">Search:</p>
                      {loc.searchable_items.map((item) => (
                        <button
                          key={item}
                          onClick={() => handleSearch(loc.id, item)}
                          className="w-full text-left text-sm p-2 bg-zinc-800/50 hover:bg-zinc-700/50 rounded transition-colors"
                        >
                          🔍 {item}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
