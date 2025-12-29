import { useState, useEffect, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { fetchGame, fetchCharacters, selectCharacter, startGame } from '../services/api';
import { useWebSocket } from '../hooks/useWebSocket';
import type { GameState, Character, WSMessage } from '../types';

export default function Lobby() {
  const { gameId } = useParams<{ gameId: string }>();
  const navigate = useNavigate();
  const playerId = sessionStorage.getItem('playerId');
  const playerName = sessionStorage.getItem('playerName');

  const [game, setGame] = useState<GameState | null>(null);
  const [characters, setCharacters] = useState<Character[]>([]);
  const [selectedChar, setSelectedChar] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  const { isConnected, addMessageHandler } = useWebSocket(gameId || null, playerId);

  const loadData = useCallback(async () => {
    if (!gameId) return;
    try {
      const [gameData, charData] = await Promise.all([
        fetchGame(gameId),
        fetchCharacters(gameId),
      ]);
      setGame(gameData);
      setCharacters(charData);

      // Check if current player has selected a character
      const currentPlayer = gameData.players.find((p: { id: string | null; }) => p.id === playerId);
      if (currentPlayer?.character_id) {
        setSelectedChar(currentPlayer.character_id);
      }
    } catch {
      setError('Failed to load game');
    } finally {
      setIsLoading(false);
    }
  }, [gameId, playerId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  useEffect(() => {
    const cleanup = addMessageHandler((message: WSMessage) => {
      if (message.type === 'player_joined' || message.type === 'player_left') {
        loadData(); // Refresh player list
      } else if (message.type === 'phase_change') {
        const payload = message.payload as { phase: string };
        if (payload.phase === 'script_reading') {
          navigate(`/game/${gameId}`);
        }
      }
    });
    return () => { cleanup(); };
  }, [addMessageHandler, gameId, navigate, loadData]);

  const handleSelectCharacter = async (characterId: string) => {
    if (!gameId || !playerId) return;

    try {
      await selectCharacter(gameId, playerId, characterId);
      setSelectedChar(characterId);
      loadData(); // Refresh to update taken status
    } catch {
      setError('Failed to select character. It may already be taken.');
      loadData();
    }
  };

  const handleStartGame = async () => {
    if (!gameId || !playerId) return;

    try {
      await startGame(gameId, playerId);
      navigate(`/game/${gameId}`);
    } catch (e) {
      setError('Cannot start game. Make sure all players have selected characters.');
    }
  };

  const isHost = game?.host_id === playerId;
  const allReady = game?.players.every(p => p.character_id) ?? false;

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-xl text-zinc-400 animate-pulse-subtle">Loading...</div>
      </div>
    );
  }

  if (!game) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="glass-card p-8 text-center">
          <p className="text-red-400 text-xl mb-4">Game not found</p>
          <button onClick={() => navigate('/')} className="btn-secondary">
            Back to Home
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="glass-card p-6 mb-6 animate-fade-in">
          <div className="flex flex-wrap justify-between items-center gap-4">
            <div>
              <h1 className="text-2xl font-bold">{game.story_title}</h1>
              <p className="text-zinc-400">
                Game Code: <span className="text-amber-400 font-mono text-lg">{gameId}</span>
                {!isConnected && <span className="ml-2 text-red-400">(Reconnecting...)</span>}
              </p>
            </div>
            <div className="text-right">
              <p className="text-sm text-zinc-400">Playing as</p>
              <p className="text-lg font-semibold text-amber-400">{playerName}</p>
            </div>
          </div>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-900/30 border border-red-700 rounded-lg text-red-300">
            {error}
          </div>
        )}

        <div className="grid lg:grid-cols-3 gap-6">
          {/* Players */}
          <div className="glass-card p-6 animate-fade-in" style={{ animationDelay: '0.1s' }}>
            <h2 className="text-xl font-semibold mb-4">
              Players ({game.players.length})
            </h2>
            <div className="space-y-3">
              {game.players.map((player) => (
                <div
                  key={player.id}
                  className={`p-3 rounded-lg border ${player.character_id
                    ? 'border-green-600 bg-green-900/20'
                    : 'border-zinc-700 bg-zinc-800/30'
                    }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-medium">
                      {player.name}
                      {player.is_host && (
                        <span className="ml-2 text-xs bg-amber-600 px-2 py-0.5 rounded">HOST</span>
                      )}
                    </span>
                    {player.character_id ? (
                      <span className="text-sm text-green-400">✓ Ready</span>
                    ) : (
                      <span className="text-sm text-zinc-500">Selecting...</span>
                    )}
                  </div>
                  {player.character_name && (
                    <p className="text-sm text-zinc-400 mt-1">as {player.character_name}</p>
                  )}
                </div>
              ))}
            </div>

            {isHost && (
              <button
                onClick={handleStartGame}
                disabled={!allReady || game.players.length < 2}
                className="btn-primary w-full mt-6 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {!allReady ? 'Waiting for players...' : 'Start Game'}
              </button>
            )}
          </div>

          {/* Character Selection */}
          <div className="lg:col-span-2 glass-card p-6 animate-fade-in" style={{ animationDelay: '0.2s' }}>
            <h2 className="text-xl font-semibold mb-4">Select Your Character</h2>
            <div className="grid sm:grid-cols-2 gap-4">
              {characters.map((char) => {
                const isTaken = char.is_taken && char.id !== selectedChar;
                const isSelected = char.id === selectedChar;

                return (
                  <button
                    key={char.id}
                    onClick={() => !isTaken && handleSelectCharacter(char.id)}
                    disabled={isTaken}
                    className={`text-left p-4 rounded-lg border transition-all ${isSelected
                      ? 'border-amber-500 bg-amber-900/20 glow-gold'
                      : isTaken
                        ? 'border-zinc-800 bg-zinc-900/30 opacity-50 cursor-not-allowed'
                        : 'border-zinc-700 bg-zinc-800/30 hover:border-zinc-600'
                      }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-semibold text-lg">
                        {char.name}
                        {char.name_cn && (
                          <span className="text-zinc-400 text-sm ml-2">{char.name_cn}</span>
                        )}
                      </span>
                      {isSelected && <span className="text-amber-400">✓</span>}
                      {isTaken && <span className="text-zinc-500 text-sm">Taken</span>}
                    </div>
                    <p className="text-sm text-zinc-400">{char.public_info}</p>
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
