import type { FormEvent } from 'react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useUser } from '../context/UserContext';
import { useLocalStorage } from '../hooks/useLocalStorage';
import { Button, Input } from '../components/ui';

const MAX_HISTORY = 5;
const HISTORY_KEY = 'spotify_profile_history';

export function Landing() {
  const navigate = useNavigate();
  const { setUsername, isLoading, error: apiError } = useUser();
  const [input, setInput] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [recentSearches, setRecentSearches] = useLocalStorage<string[]>(
    HISTORY_KEY,
    []
  );

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    const trimmedInput = input.trim();

    if (!trimmedInput) {
      setError('Please enter a username or profile URL');
      return;
    }

    setError(null);

    try {
      await setUsername(trimmedInput);

      // Save to history
      const newHistory = [
        trimmedInput,
        ...recentSearches.filter((s) => s !== trimmedInput),
      ].slice(0, MAX_HISTORY);
      setRecentSearches(newHistory);

      navigate(`/app?user=${encodeURIComponent(trimmedInput)}`);
    } catch (e) {
      // Error is already set by UserContext
    }
  };

  const handleHistoryClick = (search: string) => {
    setInput(search);
  };

  // Extract username from URL for display
  const getDisplayName = (search: string) => {
    if (search.includes('spotify.com/user/')) {
      return search.split('/user/')[1]?.split('?')[0] || search;
    }
    return search;
  };

  const displayError = error || apiError;

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-5">
      <div className="max-w-[600px] w-full text-center">
        {/* Logo/Title */}
        <div className="mb-8">
          <h1 className="text-5xl font-black text-white mb-4">
            Spotify Song Recommender
          </h1>
          <p className="text-xl text-spotify-text leading-relaxed">
            Get personalized playlist recommendations powered by AI. Enter your
            Spotify username or profile URL to get started.
          </p>
        </div>

        {/* Error Message */}
        {displayError && (
          <div className="bg-red-500/20 border border-red-500 text-red-400 px-5 py-3 rounded-lg mb-6">
            {displayError}
          </div>
        )}

        {/* Input Form */}
        <form onSubmit={handleSubmit} className="space-y-4 mb-8">
          <Input
            value={input}
            onChange={(e) => {
              setInput(e.target.value);
              setError(null);
            }}
            placeholder="Username or profile URL"
            className="text-center text-lg"
            autoFocus
          />
          <Button
            type="submit"
            size="lg"
            isLoading={isLoading}
            className="w-full"
          >
            Get Started
          </Button>
        </form>

        {/* Recent Searches */}
        {recentSearches.length > 0 && (
          <div className="mb-8">
            <p className="text-sm text-gray-500 mb-3">Recent searches:</p>
            <div className="flex flex-wrap gap-2 justify-center">
              {recentSearches.map((search) => (
                <button
                  key={search}
                  onClick={() => handleHistoryClick(search)}
                  className="bg-spotify-light-gray border border-gray-600 text-spotify-text px-4 py-2 rounded-full text-sm hover:border-spotify-green hover:text-white transition-colors"
                >
                  {getDisplayName(search)}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Features */}
        <div className="bg-spotify-gray rounded-2xl p-6 text-left">
          <h2 className="text-lg font-semibold text-white mb-4">
            What you can do:
          </h2>
          <ul className="space-y-3 text-spotify-text">
            <li className="flex items-start gap-3">
              <span className="text-spotify-green mt-1">✓</span>
              <span>
                Generate playlists based on your existing playlist's vibe
              </span>
            </li>
            <li className="flex items-start gap-3">
              <span className="text-spotify-green mt-1">✓</span>
              <span>
                Create custom playlists from text descriptions (e.g., "summer
                indie vibes")
              </span>
            </li>
            <li className="flex items-start gap-3">
              <span className="text-spotify-green mt-1">✓</span>
              <span>Use any public playlist as inspiration, not just yours</span>
            </li>
            <li className="flex items-start gap-3">
              <span className="text-spotify-green mt-1">✓</span>
              <span>Get a shareable Spotify playlist link instantly</span>
            </li>
          </ul>
        </div>

        {/* Footer */}
        <p className="text-gray-600 text-sm mt-8">
          No login required • Uses public playlist data only
        </p>
      </div>
    </div>
  );
}
