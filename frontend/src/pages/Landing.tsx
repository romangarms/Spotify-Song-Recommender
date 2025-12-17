import type { FormEvent } from 'react';
import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useUser } from '../context/UserContext';
import { useLocalStorage, useSpotifyPopupGuide } from '../hooks';
import { Button, Input, SpotifyGuideLayout, GuideInputRow } from '../components/ui';

const MAX_HISTORY = 5;
const HISTORY_KEY = 'spotify_profile_history';

const USERNAME_GUIDE_STEPS = [
  { title: 'Log in to Spotify', description: "Sign in if you haven't already" },
  { title: 'Click your profile picture', description: 'Located in the top-right corner' },
  { title: 'Click "Profile"', description: 'Opens your profile page' },
  { title: 'Click "..." then "Copy link to profile"', description: 'The three-dot menu near your name' },
  { title: 'Paste the link below', description: "We'll extract your username automatically" },
];

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
  const [helpMode, setHelpMode] = useState(false);
  const [recentSearches, setRecentSearches] = useLocalStorage<string[]>(
    HISTORY_KEY,
    []
  );

  // Check if input looks like a URL and extract username
  const extractedUsername = extractUsernameFromUrl(input);
  const isUrlInput = input.includes('open.spotify.com');

  // Handle input detected from clipboard
  const handleInputDetected = useCallback((text: string) => {
    if (!input) {
      setInput(text);
      // Auto-submit after a short delay
      setTimeout(() => {
        const form = document.querySelector('form');
        if (form) form.requestSubmit();
      }, 600);
    }
  }, [input]);

  const { openPopup, checkClipboard, closePopup } = useSpotifyPopupGuide({
    spotifyUrl: 'https://open.spotify.com',
    isValidInput: (text) => text.includes('open.spotify.com/user/'),
    onInputDetected: handleInputDetected,
  });

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

      // Close the Spotify popup if open
      closePopup();

      navigate(`/app?user=${encodeURIComponent(usernameToUse)}`);
    } catch {
      // Error is already set by UserContext
    }
  };

  const handleHistoryClick = (search: string) => {
    setInput(search);
  };

  const enterHelpMode = () => {
    setHelpMode(true);
    openPopup();
  };

  const displayError = error || apiError;

  // Help Mode: Full-page split layout with instructions on left
  if (helpMode) {
    return (
      <SpotifyGuideLayout
        title="Find Your Username"
        subtitle="Follow these steps in the Spotify window on the right:"
        steps={USERNAME_GUIDE_STEPS}
        onBack={() => setHelpMode(false)}
      >
        {/* Error Message */}
        {displayError && (
          <div className="bg-red-500/20 border border-red-500 text-red-400 px-5 py-3 rounded-lg mb-4">
            {displayError}
          </div>
        )}

        {/* Input Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <GuideInputRow
              value={input}
              onChange={(value) => {
                setInput(value);
                setError(null);
              }}
              onPaste={checkClipboard}
              placeholder="Paste your profile link here"
            />
            {isUrlInput && extractedUsername && (
              <div className="mt-2 text-sm text-spotify-green">
                Found username: <span className="font-medium">{extractedUsername}</span>
              </div>
            )}
            {isUrlInput && !extractedUsername && (
              <div className="mt-2 text-sm text-yellow-500">
                Couldn't extract username from URL. Make sure it's a profile link.
              </div>
            )}
          </div>
          <Button
            type="submit"
            size="lg"
            isLoading={isLoading}
            className="w-full"
            disabled={!input.trim()}
          >
            Get Started
          </Button>
        </form>
      </SpotifyGuideLayout>
    );
  }

  // Normal landing page
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

        {/* Primary CTA - Find Username */}
        <Button
          type="button"
          size="lg"
          onClick={enterHelpMode}
          className="w-full mb-6"
        >
          Find My Username
        </Button>

        {/* Divider */}
        <div className="flex items-center gap-4 mb-6">
          <div className="flex-1 h-px bg-gray-700" />
          <span className="text-gray-500 text-sm">or enter it directly</span>
          <div className="flex-1 h-px bg-gray-700" />
        </div>

        {/* Secondary - Manual Input */}
        <form onSubmit={handleSubmit} className="space-y-4 mb-8">
          <div className="relative">
            <Input
              value={input}
              onChange={(e) => {
                setInput(e.target.value);
                setError(null);
              }}
              placeholder="Spotify username or profile URL"
              className="text-center text-lg"
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
            variant="secondary"
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
