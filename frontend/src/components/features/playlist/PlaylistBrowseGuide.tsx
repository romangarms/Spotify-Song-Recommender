import type { FormEvent } from 'react';
import { useState, useCallback } from 'react';
import { Button, SpotifyGuideLayout, GuideInputRow } from '../../ui';
import { useGeneration } from '../../../context/GenerationContext';
import { useSpotifyPopupGuide } from '../../../hooks';
import { api } from '../../../api/client';

// Open Spotify in a popup window positioned on the right half of the screen
export function openSpotifyPlaylistBrowser(username?: string): Window | null {
  const width = Math.floor(window.screen.availWidth / 2);
  const height = window.screen.availHeight;
  const left = Math.floor(window.screen.availWidth / 2);
  const url = username
    ? `https://open.spotify.com/user/${username}/playlists`
    : 'https://open.spotify.com';
  return window.open(
    url,
    'spotify',
    `width=${width},height=${height},left=${left},top=0`
  );
}

const PLAYLIST_GUIDE_STEPS = [
  { title: 'Find the playlist you want', description: "Browse your library or use Spotify's search" },
  { title: 'Click "..." next to the playlist', description: 'The three-dot menu with more options' },
  { title: 'Click "Share" → "Copy link to playlist"', description: 'This copies the link to your clipboard' },
  { title: 'Paste it below', description: "We'll auto-detect it when you switch back, or paste manually" },
];

// Check if input looks like a valid Spotify playlist URL
function isValidPlaylistUrl(input: string): boolean {
  return input.includes('spotify.com/playlist/') || input.includes('spotify:playlist:');
}

export function PlaylistBrowseGuide() {
  const { setPlaylistBrowseMode, setSelectedPlaylist } = useGeneration();
  const [url, setUrl] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Check URL format for immediate feedback
  const isUrlInput = url.includes('spotify.com') || url.includes('spotify:');
  const isValidUrl = isValidPlaylistUrl(url);

  // Handle input detected from clipboard
  const handleInputDetected = useCallback((text: string) => {
    if (!url) {
      setUrl(text);
      // Auto-submit after a short delay (same as Landing page)
      setTimeout(() => {
        const form = document.querySelector('form');
        if (form) form.requestSubmit();
      }, 600);
    }
  }, [url]);

  const { checkClipboard } = useSpotifyPopupGuide({
    spotifyUrl: 'https://open.spotify.com',
    isValidInput: isValidPlaylistUrl,
    onInputDetected: handleInputDetected,
  });

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    const trimmedUrl = url.trim();

    if (!trimmedUrl) {
      setError('Please enter a playlist URL');
      return;
    }

    if (!isValidPlaylistUrl(trimmedUrl)) {
      setError('Please enter a valid Spotify playlist URL');
      return;
    }

    setError(null);
    setIsLoading(true);

    try {
      const result = await api.validatePlaylistUrl(trimmedUrl);
      const imageUrl = result.images?.[0]?.url;
      setSelectedPlaylist(result.playlist_id, result.playlist_name, trimmedUrl, imageUrl);
      setPlaylistBrowseMode(false);
    } catch (e) {
      const errorMessage = e instanceof Error ? e.message : 'Could not access playlist';
      setError(errorMessage);
      setIsLoading(false);
    }
  };

  return (
    <SpotifyGuideLayout
      title="Find Your Playlist"
      subtitle="Follow these steps in the Spotify window on the right:"
      steps={PLAYLIST_GUIDE_STEPS}
      tip='If the playlist is private, click "..." → "Make public" first, then copy the link.'
      onBack={() => setPlaylistBrowseMode(false)}
    >
      {error && (
        <div className="bg-red-500/20 border border-red-500 text-red-400 px-5 py-3 rounded-lg mb-4">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <GuideInputRow
            value={url}
            onChange={(value) => {
              setUrl(value);
              setError(null);
            }}
            onPaste={checkClipboard}
            placeholder="Paste your playlist link here"
          />
          {isUrlInput && isValidUrl && (
            <div className="mt-2 text-sm text-spotify-green">
              Spotify playlist URL detected
            </div>
          )}
          {isUrlInput && !isValidUrl && (
            <div className="mt-2 text-sm text-yellow-500">
              This doesn't look like a playlist URL. Make sure it's a playlist link.
            </div>
          )}
        </div>
        <Button
          type="submit"
          size="lg"
          isLoading={isLoading}
          className="w-full"
          disabled={!url.trim()}
        >
          Get Started
        </Button>
      </form>
    </SpotifyGuideLayout>
  );
}
