import { useState, useEffect, useRef } from 'react';
import { Input } from '../../ui';
import { useGeneration } from '../../../context/GenerationContext';
import { api } from '../../../api/client';

type ValidationStatus = {
  type: 'idle' | 'loading' | 'success' | 'error';
  message: string;
};

export function PlaylistUrlInput() {
  const [url, setUrl] = useState('');
  const [status, setStatus] = useState<ValidationStatus>({
    type: 'idle',
    message: '',
  });
  const { setSelectedPlaylist } = useGeneration();
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Debounced URL validation
  useEffect(() => {
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }

    if (!url.trim()) {
      setStatus({ type: 'idle', message: '' });
      return;
    }

    // Check if it looks like a Spotify URL
    if (!url.includes('spotify.com/playlist/') && !url.includes('spotify:playlist:')) {
      setStatus({
        type: 'error',
        message: 'Please enter a valid Spotify playlist URL',
      });
      return;
    }

    setStatus({ type: 'loading', message: 'Checking...' });

    debounceRef.current = setTimeout(async () => {
      try {
        const result = await api.validatePlaylistUrl(url);
        setStatus({
          type: 'success',
          message: `Found: ${result.playlist_name} (${result.tracks_total} tracks)`,
        });
        setSelectedPlaylist(result.playlist_id, result.playlist_name);
      } catch (e) {
        const errorMessage =
          e instanceof Error ? e.message : 'Could not access playlist';
        setStatus({ type: 'error', message: errorMessage });
        setSelectedPlaylist(null);
      }
    }, 800);

    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
    };
  }, [url, setSelectedPlaylist]);

  const handleClear = () => {
    setUrl('');
    setStatus({ type: 'idle', message: '' });
    setSelectedPlaylist(null);
  };

  return (
    <div className="space-y-2">
      <div className="relative">
        <Input
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://open.spotify.com/playlist/..."
          className="pr-10"
        />
        {url && (
          <button
            onClick={handleClear}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-spotify-text hover:text-white"
            aria-label="Clear"
          >
            ✕
          </button>
        )}
      </div>

      {status.message && (
        <p
          className={`text-sm ${
            status.type === 'success'
              ? 'text-spotify-green'
              : status.type === 'error'
              ? 'text-red-500'
              : 'text-spotify-text'
          }`}
        >
          {status.message}
        </p>
      )}
    </div>
  );
}
