import type { FormEvent } from 'react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useLocalStorage } from '../hooks';
import { Button, Input } from '../components/ui';
import { api } from '../api/client';

const MAX_HISTORY = 5;
const HISTORY_KEY = 'spotify_playlist_history_v2';
const USER_HISTORY_KEY = 'spotify_user_history_v1';
const MAX_USER_HISTORY = 5;

interface PlaylistHistoryItem {
  url: string;
  name: string;
  playlistId: string;
}

interface UserHistoryItem {
  username: string;
  displayName: string;
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
  const [recentUsers, setRecentUsers] = useLocalStorage<UserHistoryItem[]>(
    USER_HISTORY_KEY,
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

      // Save playlist to history
      const newPlaylistHistory = [
        {
          url: trimmedInput,
          name: ownerData.playlist_name,
          playlistId: ownerData.playlist_id,
        },
        ...recentSearches.filter((item) => item.url !== trimmedInput),
      ].slice(0, MAX_HISTORY);
      setRecentSearches(newPlaylistHistory);

      // Save user to history
      const newUserHistory = [
        {
          username: ownerData.username,
          displayName: ownerData.display_name,
        },
        ...recentUsers.filter((user) => user.username !== ownerData.username),
      ].slice(0, MAX_USER_HISTORY);
      setRecentUsers(newUserHistory);

      // Navigate to app with username AND playlist ID for auto-selection
      navigate(`/app?user=${encodeURIComponent(ownerData.username)}&playlist=${encodeURIComponent(ownerData.playlist_id)}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load playlist');
    } finally {
      setIsLoading(false);
    }
  };

  const handlePlaylistClick = async (item: PlaylistHistoryItem) => {
    setIsLoading(true);
    setError(null);

    try {
      const ownerData = await api.getPlaylistOwner(item.url);
      navigate(`/app?user=${encodeURIComponent(ownerData.username)}&playlist=${encodeURIComponent(item.playlistId)}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load playlist');
    } finally {
      setIsLoading(false);
    }
  };

  const handleUserClick = (username: string) => {
    navigate(`/app?user=${encodeURIComponent(username)}`);
  };

  const handleRemovePlaylist = (e: React.MouseEvent, playlistId: string) => {
    e.stopPropagation();
    setRecentSearches(recentSearches.filter(item => item.playlistId !== playlistId));
  };

  const handleRemoveUser = (e: React.MouseEvent, username: string) => {
    e.stopPropagation();
    setRecentUsers(recentUsers.filter(user => user.username !== username));
  };

  const handleClearAll = () => {
    setRecentSearches([]);
    setRecentUsers([]);
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
            Discover new music based on your favorite playlists. Paste a Spotify playlist URL to generate recommendations powered by the Logic API.
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

        {/* Recent Playlists and Users */}
        {(recentSearches.length > 0 || recentUsers.length > 0) && (
          <div className="mb-8">
            <div className="flex items-center justify-center gap-3 mb-4">
              <p className="text-sm text-gray-500">Recent:</p>
              <button
                onClick={handleClearAll}
                className="text-xs px-3 py-1 bg-spotify-light-gray border border-gray-600 text-gray-400 hover:text-red-400 hover:border-red-400 rounded-full transition-colors"
              >
                Clear all
              </button>
            </div>
            <div className="grid grid-cols-2 gap-4">
              {/* Recent Playlists Column */}
              <div>
                <p className="text-xs text-gray-500 mb-2 text-center">Playlists</p>
                <div className="space-y-1">
                  {recentSearches.length > 0 ? (
                    recentSearches.map((item, index) => (
                      <button
                        key={index}
                        onClick={() => handlePlaylistClick(item)}
                        className="relative w-full bg-spotify-light-gray border border-gray-600 text-spotify-text px-3 py-2 pr-8 rounded-lg text-sm hover:border-spotify-green hover:text-white transition-colors text-left"
                        title={item.url}
                      >
                        <div className="truncate">{item.name}</div>
                        <span
                          onClick={(e) => handleRemovePlaylist(e, item.playlistId)}
                          className="absolute right-2 top-1/2 -translate-y-1/2 text-white hover:text-red-400 transition-colors cursor-pointer"
                          aria-label="Remove"
                        >
                          ✕
                        </span>
                      </button>
                    ))
                  ) : (
                    <p className="text-xs text-gray-600 text-center py-4">No recent playlists</p>
                  )}
                </div>
              </div>

              {/* Recent Users Column */}
              <div>
                <p className="text-xs text-gray-500 mb-2 text-center">Users</p>
                <div className="space-y-1">
                  {recentUsers.length > 0 ? (
                    recentUsers.map((user, index) => (
                      <button
                        key={index}
                        onClick={() => handleUserClick(user.username)}
                        className="relative w-full bg-spotify-light-gray border border-gray-600 text-spotify-text px-3 py-2 pr-8 rounded-lg text-sm hover:border-spotify-green hover:text-white transition-colors text-left"
                        title={`@${user.username}`}
                      >
                        <div className="truncate">{user.displayName}</div>
                        <span
                          onClick={(e) => handleRemoveUser(e, user.username)}
                          className="absolute right-2 top-1/2 -translate-y-1/2 text-white hover:text-red-400 transition-colors cursor-pointer"
                          aria-label="Remove"
                        >
                          ✕
                        </span>
                      </button>
                    ))
                  ) : (
                    <p className="text-xs text-gray-600 text-center py-4">No recent users</p>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* How it works */}
        <div className="bg-spotify-gray rounded-2xl p-6 text-left">
          <h2 className="text-lg font-semibold text-white mb-4">
            How it works:
          </h2>
          <ol className="space-y-3 text-spotify-text">
            <li className="flex items-start gap-3">
              <span className="text-spotify-green font-semibold min-w-6">1.</span>
              <span>Paste a Spotify playlist URL to use as input</span>
            </li>
            <li className="flex items-start gap-3">
              <span className="text-spotify-green font-semibold min-w-6">2.</span>
              <span>An LLM analyzes your music taste and playlist themes</span>
            </li>
            <li className="flex items-start gap-3">
              <span className="text-spotify-green font-semibold min-w-6">3.</span>
              <span>The AI generates 15 personalized song recommendations</span>
            </li>
            <li className="flex items-start gap-3">
              <span className="text-spotify-green font-semibold min-w-6">4.</span>
              <span>A new Spotify playlist is created with your recommendations</span>
            </li>
          </ol>
        </div>

        {/* Footer */}
        <p className="text-gray-600 text-sm mt-8">
          No login required • Uses public playlist data only
        </p>
      </div>
    </div>
  );
}
