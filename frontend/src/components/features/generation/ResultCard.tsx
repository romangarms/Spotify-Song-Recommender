import { useGeneration } from '../../../context/GenerationContext';
import { Button } from '../../ui';
import { TrackList } from './TrackList';

export function ResultCard() {
  const { state, reset } = useGeneration();

  // Idle state
  if (state.status === 'idle') {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <div className="text-6xl mb-4">🎵</div>
        <h3 className="text-xl font-semibold text-white mb-2">
          Ready to Generate
        </h3>
        <p className="text-spotify-text max-w-xs">
          Select a playlist or describe your ideal playlist, then click Generate
          to create a new playlist powered by AI.
        </p>
      </div>
    );
  }

  // Loading state
  if (state.status === 'loading') {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <div className="w-16 h-16 border-4 border-spotify-green border-t-transparent rounded-full animate-spin mb-4" />
        <h3 className="text-xl font-semibold text-white mb-2">
          Generating Your Playlist...
        </h3>
        <p className="text-spotify-text max-w-xs">
          This may take a moment while we analyze and find the perfect tracks
          for you.
        </p>
      </div>
    );
  }

  // Error state
  if (state.status === 'error') {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <div className="text-6xl mb-4">😕</div>
        <h3 className="text-xl font-semibold text-white mb-2">
          Something Went Wrong
        </h3>
        <p className="text-red-500 mb-4">{state.error}</p>
        <Button variant="secondary" onClick={reset}>
          Try Again
        </Button>
      </div>
    );
  }

  // Success state
  const result = state.result!;

  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-xl font-bold text-white mb-2">{result.title}</h3>
        <p className="text-spotify-text text-sm">{result.description}</p>
      </div>

      {/* Full Track List */}
      <TrackList tracks={result.tracks} />

      {/* Actions */}
      <div className="space-y-2 pt-4">
        <Button
          as="a"
          href={result.playlist_url}
          target="_blank"
          rel="noopener noreferrer"
          className="w-full"
          size="lg"
        >
          Open in Spotify
        </Button>

        <Button
          variant="secondary"
          onClick={reset}
          className="w-full"
          size="md"
        >
          Generate Another
        </Button>
      </div>

      {/* Not found tracks info */}
      {result.not_found && result.not_found.length > 0 && (
        <div className="pt-4 border-t border-gray-700">
          <p className="text-spotify-text text-xs">
            {result.not_found.length} track(s) couldn't be found on Spotify
          </p>
        </div>
      )}
    </div>
  );
}
