import { useState, useRef, useEffect } from 'react';
import type { SeedTrack } from '../../../types';
import { api } from '../../../api/client';
import { useGeneration } from '../../../context/GenerationContext';

const SEARCH_DEBOUNCE_MS = 300;

export function SongSeedInput() {
  const { seedTracks, addSeedTracks, removeSeedTrack, clearSeedTracks } =
    useGeneration();

  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SeedTrack[]>([]);
  const [isBusy, setIsBusy] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const requestId = useRef(0);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleLinks = async (text: string) => {
    setIsBusy(true);
    setError(null);
    setNotice(null);
    try {
      const { tracks, not_found, truncated } = await api.resolveTracks(text);
      addSeedTracks(tracks);
      setQuery('');
      setResults([]);

      const parts = [`Added ${tracks.length} song${tracks.length === 1 ? '' : 's'}`];
      if (not_found.length) parts.push(`${not_found.length} couldn't be found`);
      if (truncated) parts.push('list was capped at 100');
      setNotice(parts.join(' · '));
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not read those links');
    } finally {
      setIsBusy(false);
      inputRef.current?.focus();
    }
  };

  const handlePaste = (e: React.ClipboardEvent<HTMLInputElement>) => {
    const text = e.clipboardData.getData('text');
    if (!text.includes('spotify.com/track/') && !text.includes('spotify:track:')) {
      return;
    }
    e.preventDefault();
    handleLinks(text);
  };

  useEffect(() => {
    const trimmed = query.trim();
    if (trimmed.length < 2) {
      setResults([]);
      return;
    }

    const id = ++requestId.current;
    const timer = setTimeout(async () => {
      try {
        const { tracks } = await api.searchTracks(trimmed);
        if (id === requestId.current) setResults(tracks);
      } catch {
        if (id === requestId.current) setResults([]);
      }
    }, SEARCH_DEBOUNCE_MS);

    return () => clearTimeout(timer);
  }, [query]);

  const pick = (track: SeedTrack) => {
    addSeedTracks([track]);
    setQuery('');
    setResults([]);
    setNotice(null);
    inputRef.current?.focus();
  };

  return (
    <div className="flex flex-col h-full min-h-0">
      <h3 className="text-white font-semibold mb-2">Pick songs to build from:</h3>
      <p className="text-spotify-text text-sm mb-3">
        Search by name, or paste Spotify song links — select several songs in
        Spotify, right-click, Share, Copy links, and paste them all at once.
      </p>

      <div className="relative flex-shrink-0">
        <input
          ref={inputRef}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onPaste={handlePaste}
          disabled={isBusy}
          placeholder={isBusy ? 'Looking up songs…' : 'Search a song or paste Spotify links'}
          className="w-full px-4 py-3 bg-spotify-light-gray text-white rounded-lg border border-gray-600 placeholder-spotify-text focus:border-spotify-green focus:outline-none transition-colors disabled:opacity-60"
        />

        {results.length > 0 && (
          <ul className="absolute z-10 mt-1 w-full max-h-64 overflow-y-auto bg-spotify-light-gray border border-gray-600 rounded-lg shadow-lg">
            {results.map((track) => (
              <li key={track.id}>
                <button
                  type="button"
                  onClick={() => pick(track)}
                  className="w-full flex items-center gap-3 p-2 text-left hover:bg-gray-700 transition-colors"
                >
                  {track.image ? (
                    <img src={track.image} alt="" className="w-9 h-9 rounded flex-shrink-0" />
                  ) : (
                    <div className="w-9 h-9 rounded bg-gray-700 flex items-center justify-center flex-shrink-0">
                      <span className="text-spotify-text text-xs">♪</span>
                    </div>
                  )}
                  <div className="min-w-0">
                    <p className="text-white text-sm truncate">{track.name}</p>
                    <p className="text-spotify-text text-xs truncate">{track.artist}</p>
                  </div>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      {error && <p className="mt-2 text-sm text-red-500">{error}</p>}
      {notice && !error && <p className="mt-2 text-sm text-spotify-text">{notice}</p>}

      <div className="flex items-center justify-between mt-4 mb-2 flex-shrink-0">
        <h4 className="text-white font-semibold">
          Your songs ({seedTracks.length})
        </h4>
        {seedTracks.length > 0 && (
          <button
            type="button"
            onClick={clearSeedTracks}
            className="text-spotify-text text-sm hover:text-white transition-colors"
          >
            Clear all
          </button>
        )}
      </div>

      <div className="flex-1 min-h-0 overflow-y-auto pr-1">
        {seedTracks.length === 0 ? (
          <p className="text-spotify-text text-sm py-4">
            No songs yet. Add a few that capture the vibe you want.
          </p>
        ) : (
          <ul className="space-y-1">
            {seedTracks.map((track) => (
              <li
                key={track.id}
                className="flex items-center gap-3 p-2 hover:bg-spotify-light-gray rounded transition-colors group"
              >
                {track.image ? (
                  <img src={track.image} alt="" className="w-10 h-10 rounded flex-shrink-0" />
                ) : (
                  <div className="w-10 h-10 rounded bg-spotify-light-gray flex items-center justify-center flex-shrink-0">
                    <span className="text-spotify-text text-xs">♪</span>
                  </div>
                )}
                <div className="flex-1 min-w-0">
                  <p className="text-white truncate text-sm">{track.name}</p>
                  <p className="text-spotify-text text-xs truncate">{track.artist}</p>
                </div>
                <button
                  type="button"
                  onClick={() => removeSeedTrack(track.id)}
                  aria-label={`Remove ${track.name}`}
                  className="text-spotify-text hover:text-white px-2 opacity-0 group-hover:opacity-100 focus:opacity-100 transition-opacity"
                >
                  ✕
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
