import type { FormEvent } from 'react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useUser } from '../context/UserContext';
import { useLocalStorage } from '../hooks/useLocalStorage';
import { Button, Input } from '../components/ui';

const MAX_HISTORY = 5;
const HISTORY_KEY = 'spotify_profile_history';

// Extract username from Spotify URL
function extractUsernameFromUrl(input: string): string | null {
  if (input.includes('open.spotify.com/user/')) {
    const match = input.match(/open\.spotify\.com\/user\/([a-zA-Z0-9_.-]+)/);
    return match ? match[1] : null;
  }
  return null;
}

export function Landing() {
  const navigate = useNavigate();
  const { setUsername, isLoading, error: apiError } = useUser();
  const [input, setInput] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [showSpotify, setShowSpotify] = useState(false);
  const [recentSearches, setRecentSearches] = useLocalStorage<string[]>(
    HISTORY_KEY,
    []
  );

  // Check if input looks like a URL and extract username
  const extractedUsername = extractUsernameFromUrl(input);
  const isUrlInput = input.includes('open.spotify.com');

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    const trimmedInput = input.trim();

    if (!trimmedInput) {
      setError('Please enter a username');
      return;
    }

    // Use extracted username if it's a URL, otherwise use raw input
    const usernameToUse = extractedUsername || trimmedInput;

    setError(null);

    try {
      await setUsername(usernameToUse);

      // Save to history (save the username, not the full URL)
      const newHistory = [
        usernameToUse,
        ...recentSearches.filter((s) => s !== usernameToUse),
      ].slice(0, MAX_HISTORY);
      setRecentSearches(newHistory);

      navigate(`/app?user=${encodeURIComponent(usernameToUse)}`);
    } catch (e) {
      // Error is already set by UserContext
    }
  };

  const handleHistoryClick = (search: string) => {
    setInput(search);
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
            Get personalized playlist recommendations powered by the Logic API. Enter your
            Spotify username to get started.
          </p>
        </div>

        {/* Error Message */}
        {displayError && (
          <div className="bg-red-500/20 border border-red-500 text-red-400 px-5 py-3 rounded-lg mb-6">
            {displayError}
          </div>
        )}

        {/* Input Form */}
        <form onSubmit={handleSubmit} className="space-y-4 mb-4">
          <div className="relative">
            <Input
              value={input}
              onChange={(e) => {
                setInput(e.target.value);
                setError(null);
              }}
              placeholder="Spotify username"
              className="text-center text-lg"
              autoFocus
            />
            {/* Show extracted username when URL is pasted */}
            {isUrlInput && extractedUsername && (
              <div className="mt-2 text-sm text-spotify-green">
                Found username: <span className="font-medium">{extractedUsername}</span>
              </div>
            )}
            {isUrlInput && !extractedUsername && (
              <div className="mt-2 text-sm text-yellow-500">
                Couldn't extract username from URL. Please paste a profile URL.
              </div>
            )}
          </div>
          <Button
            type="submit"
            size="lg"
            isLoading={isLoading}
            className="w-full"
          >
            Get Started
          </Button>
        </form>

        {/* Help Section */}
        <div className="mb-8 bg-spotify-gray rounded-xl p-5 text-left">
          <p className="text-white font-medium mb-3">Don't know your username?</p>
          <ol className="space-y-2 text-spotify-text text-sm">
            <li className="flex gap-3">
              <span className="text-spotify-green font-medium">1.</span>
              <span>
                <button
                  type="button"
                  onClick={() => setShowSpotify(!showSpotify)}
                  className="text-spotify-green hover:underline"
                >
                  {showSpotify ? 'Hide Spotify' : 'Open Spotify'}
                </button>
                {' '}and log in
              </span>
            </li>
            <li className="flex gap-3">
              <span className="text-spotify-green font-medium">2.</span>
              <span>Click your profile icon (top right)</span>
            </li>
            <li className="flex gap-3">
              <span className="text-spotify-green font-medium">3.</span>
              <span>Click "Profile"</span>
            </li>
            <li className="flex gap-3">
              <span className="text-spotify-green font-medium">4.</span>
              <span>Click "..." → "Copy link to profile"</span>
            </li>
            <li className="flex gap-3">
              <span className="text-spotify-green font-medium">5.</span>
              <span>Paste the link above</span>
            </li>
          </ol>

          {showSpotify && (
            <div className="mt-4 rounded-lg overflow-hidden border border-gray-700">
              <iframe
                src="https://open.spotify.com"
                title="Spotify"
                className="w-full h-[500px]"
                sandbox="allow-same-origin allow-scripts allow-popups allow-forms"
              />
            </div>
          )}
        </div>

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
                  {search}
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
