import type { FormEvent } from 'react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useLocalStorage } from '../hooks';
import { Button, Input } from '../components/ui';
import { api } from '../api/client';

const MAX_HISTORY = 5;
const HISTORY_KEY = 'spotify_playlist_history_v2';

interface PlaylistHistoryItem {
  url: string;
  name: string;
  playlistId: string;
}

// Extract playlist ID from Spotify URL
function extractPlaylistIdFromUrl(input: string): string | null {
  if (input.includes('open.spotify.com/playlist/')) {
    const match = input.match(/open\.spotify\.com\/playlist\/([a-zA-Z0-9]+)/);
    return match ? match[1] : null;
  }
  if (input.includes('spotify:playlist:')) {
    const match = input.match(/spotify:playlist:([a-zA-Z0-9]+)/);
    return match ? match[1] : null;
  }
  return null;
}

export function Landing() {
  const navigate = useNavigate();
  const [input, setInput] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [recentSearches, setRecentSearches] = useLocalStorage<PlaylistHistoryItem[]>(
    HISTORY_KEY,
    []
  );

  // Check if input looks like a playlist URL
  const extractedPlaylistId = extractPlaylistIdFromUrl(input);
  const isPlaylistUrl = extractedPlaylistId !== null;

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    const trimmedInput = input.trim();

    if (!trimmedInput) {
      setError('Please enter a playlist URL');
      return;
    }

    setError(null);
    setIsLoading(true);

    try {
      // Get playlist owner
      const ownerData = await api.getPlaylistOwner(trimmedInput);

      // Save to history with metadata
      const newHistory = [
        {
          url: trimmedInput,
          name: ownerData.playlist_name,
          playlistId: ownerData.playlist_id,
        },
        ...recentSearches.filter((item) => item.url !== trimmedInput),
      ].slice(0, MAX_HISTORY);
      setRecentSearches(newHistory);

      // Navigate to app with username AND playlist ID for auto-selection
      navigate(`/app?user=${encodeURIComponent(ownerData.username)}&playlist=${encodeURIComponent(ownerData.playlist_id)}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load playlist');
    } finally {
      setIsLoading(false);
    }
  };

  const handleHistoryClick = (url: string) => {
    setInput(url);
  };

  // Main landing page
  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-5">
      <div className="max-w-[600px] w-full text-center">
        {/* Logo/Title */}
        <div className="mb-8">
          <h1 className="text-5xl font-black text-white mb-4">
            Spotify Song Recommender
          </h1>
          <p className="text-xl text-spotify-text leading-relaxed">
            Get personalized playlist recommendations powered by AI. Paste a Spotify playlist URL to get started.
          </p>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-500/20 border border-red-500 text-red-400 px-5 py-3 rounded-lg mb-6">
            {error}
          </div>
        )}

        {/* Primary Input */}
        <form onSubmit={handleSubmit} className="space-y-4 mb-6">
          <div className="relative">
            <Input
              value={input}
              onChange={(e) => {
                setInput(e.target.value);
                setError(null);
              }}
              placeholder="Paste Spotify playlist URL"
              className="text-center text-lg"
            />
            {/* Show extracted playlist ID when URL is pasted */}
            {isPlaylistUrl && (
              <div className="mt-2 text-sm text-spotify-green">
                Found playlist! Ready to go
              </div>
            )}
            {input && !isPlaylistUrl && (
              <div className="mt-2 text-sm text-yellow-500">
                Couldn't find a valid playlist URL. Please paste a Spotify playlist link.
              </div>
            )}
          </div>
          <Button
            type="submit"
            size="lg"
            isLoading={isLoading}
            className="w-full"
            disabled={!input.trim() || !isPlaylistUrl}
          >
            Get Started
          </Button>
        </form>

        {/* Recent Playlists */}
        {recentSearches.length > 0 && (
          <div className="mb-8">
            <p className="text-sm text-gray-500 mb-3">Recent playlists:</p>
            <div className="flex flex-wrap gap-2 justify-center">
              {recentSearches.map((item, index) => (
                <button
                  key={index}
                  onClick={() => handleHistoryClick(item.url)}
                  className="bg-spotify-light-gray border border-gray-600 text-spotify-text px-4 py-2 rounded-full text-sm hover:border-spotify-green hover:text-white transition-colors"
                  title={item.url}
                >
                  {item.name}
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
              <span>Paste any public Spotify playlist to get started</span>
            </li>
            <li className="flex items-start gap-3">
              <span className="text-spotify-green mt-1">✓</span>
              <span>Generate new playlists based on existing ones</span>
            </li>
            <li className="flex items-start gap-3">
              <span className="text-spotify-green mt-1">✓</span>
              <span>Use any public playlist as inspiration</span>
            </li>
            <li className="flex items-start gap-3">
              <span className="text-spotify-green mt-1">✓</span>
              <span>Get shareable Spotify links instantly</span>
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
