import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchStories, createGame } from '../services/api';
import type { Story } from '../types';

export default function Home() {
  const navigate = useNavigate();
  const [stories, setStories] = useState<Story[]>([]);
  const [selectedStory, setSelectedStory] = useState<Story | null>(null);
  const [hostName, setHostName] = useState('');
  const [joinCode, setJoinCode] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchStories()
      .then(setStories)
      .catch(() => setError('Failed to load stories. Is the backend running?'));
  }, []);

  const handleCreateGame = async () => {
    if (!selectedStory || !hostName.trim()) {
      setError('Please select a story and enter your name');
      return;
    }

    setIsCreating(true);
    setError('');

    try {
      const result = await createGame(selectedStory.id, hostName.trim());
      // Store player info in sessionStorage
      sessionStorage.setItem('playerId', result.player_id);
      sessionStorage.setItem('playerName', hostName.trim());
      navigate(`/lobby/${result.game_id}`);
    } catch (e) {
      setError('Failed to create game');
    } finally {
      setIsCreating(false);
    }
  };

  const handleJoinGame = () => {
    if (!joinCode.trim()) {
      setError('Please enter a game code');
      return;
    }
    navigate(`/join/${joinCode.trim()}`);
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="max-w-4xl w-full">
        {/* Header */}
        <div className="text-center mb-12 animate-fade-in">
          <h1 className="text-6xl font-bold mb-4 bg-gradient-to-r from-red-500 via-amber-500 to-red-500 bg-clip-text text-transparent">
            剧本杀
          </h1>
          <p className="text-2xl text-zinc-400">Murder Mystery</p>
          <p className="text-zinc-500 mt-2">Uncover the truth. Solve the mystery.</p>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-900/30 border border-red-700 rounded-lg text-red-300 text-center">
            {error}
          </div>
        )}

        <div className="grid md:grid-cols-2 gap-8">
          {/* Create Game */}
          <div className="glass-card p-8 animate-fade-in" style={{ animationDelay: '0.1s' }}>
            <h2 className="text-2xl font-semibold mb-6 flex items-center gap-3">
              <span className="w-10 h-10 rounded-full bg-red-600 flex items-center justify-center text-lg">🎭</span>
              Create Game
            </h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm text-zinc-400 mb-2">Your Name</label>
                <input
                  type="text"
                  value={hostName}
                  onChange={(e) => setHostName(e.target.value)}
                  placeholder="Enter your name..."
                  className="input-dark w-full"
                  maxLength={20}
                />
              </div>

              <div>
                <label className="block text-sm text-zinc-400 mb-2">Select Story</label>
                <div className="space-y-2 max-h-60 overflow-y-auto pr-2">
                  {stories.length === 0 ? (
                    <p className="text-zinc-500 text-sm">Loading stories...</p>
                  ) : (
                    stories.map((story) => (
                      <button
                        key={story.id}
                        onClick={() => setSelectedStory(story)}
                        className={`w-full text-left p-4 rounded-lg border transition-all ${selectedStory?.id === story.id
                            ? 'border-red-500 bg-red-900/20 glow-red'
                            : 'border-zinc-700 bg-zinc-800/30 hover:border-zinc-600'
                          }`}
                      >
                        <div className="font-medium">
                          {story.title}
                          {story.title_cn && <span className="text-zinc-400 ml-2">{story.title_cn}</span>}
                        </div>
                        <div className="text-sm text-zinc-500 mt-1">
                          {story.player_count.min}-{story.player_count.max} players • {story.duration_minutes} min • {story.difficulty}
                        </div>
                      </button>
                    ))
                  )}
                </div>
              </div>

              <button
                onClick={handleCreateGame}
                disabled={isCreating || !selectedStory || !hostName.trim()}
                className="btn-primary w-full disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isCreating ? 'Creating...' : 'Create Game'}
              </button>
            </div>
          </div>

          {/* Join Game */}
          <div className="glass-card p-8 animate-fade-in" style={{ animationDelay: '0.2s' }}>
            <h2 className="text-2xl font-semibold mb-6 flex items-center gap-3">
              <span className="w-10 h-10 rounded-full bg-amber-600 flex items-center justify-center text-lg">🔍</span>
              Join Game
            </h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm text-zinc-400 mb-2">Game Code</label>
                <input
                  type="text"
                  value={joinCode}
                  onChange={(e) => setJoinCode(e.target.value.toUpperCase())}
                  placeholder="Enter game code..."
                  className="input-dark w-full text-center text-2xl tracking-widest"
                  maxLength={10}
                />
              </div>

              <button onClick={handleJoinGame} className="btn-gold w-full">
                Join Game
              </button>
            </div>

            <div className="mt-8 p-4 bg-zinc-800/30 rounded-lg">
              <h3 className="font-medium mb-2">How to Play</h3>
              <ol className="text-sm text-zinc-400 space-y-1 list-decimal list-inside">
                <li>Create or join a game</li>
                <li>Select your character</li>
                <li>Read your secret script</li>
                <li>Investigate and find clues</li>
                <li>Discuss with other players</li>
                <li>Vote for the culprit</li>
              </ol>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
