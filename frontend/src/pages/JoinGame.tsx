import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { joinGame } from '../services/api';

export default function JoinGame() {
  const { gameId } = useParams<{ gameId: string }>();
  const navigate = useNavigate();
  const [playerName, setPlayerName] = useState('');
  const [isJoining, setIsJoining] = useState(false);
  const [error, setError] = useState('');

  const handleJoin = async () => {
    if (!playerName.trim() || !gameId) {
      setError('Please enter your name');
      return;
    }

    setIsJoining(true);
    setError('');

    try {
      const result = await joinGame(gameId, playerName.trim());
      sessionStorage.setItem('playerId', result.player_id);
      sessionStorage.setItem('playerName', playerName.trim());
      navigate(`/lobby/${gameId}`);
    } catch {
      setError('Failed to join game. Check the game code and try again.');
    } finally {
      setIsJoining(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="glass-card p-8 max-w-md w-full animate-fade-in">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold mb-2">Join Game</h1>
          <p className="text-zinc-400">
            Game Code: <span className="text-amber-400 font-mono text-xl">{gameId}</span>
          </p>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-900/30 border border-red-700 rounded-lg text-red-300 text-center">
            {error}
          </div>
        )}

        <div className="space-y-4">
          <div>
            <label className="block text-sm text-zinc-400 mb-2">Your Name</label>
            <input
              type="text"
              value={playerName}
              onChange={(e) => setPlayerName(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleJoin()}
              placeholder="Enter your name..."
              className="input-dark w-full text-center text-xl"
              maxLength={20}
              autoFocus
            />
          </div>

          <button
            onClick={handleJoin}
            disabled={isJoining || !playerName.trim()}
            className="btn-gold w-full disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isJoining ? 'Joining...' : 'Join Game'}
          </button>

          <button
            onClick={() => navigate('/')}
            className="btn-secondary w-full"
          >
            Back to Home
          </button>
        </div>
      </div>
    </div>
  );
}
