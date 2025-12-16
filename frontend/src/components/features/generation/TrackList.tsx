import type { Track } from '../../../types';

interface TrackListProps {
  tracks: Track[];
}

export function TrackList({ tracks }: TrackListProps) {
  return (
    <div className="space-y-2">
      <h4 className="text-white font-semibold">Tracks ({tracks.length})</h4>
      <div className="space-y-1 max-h-[400px] overflow-y-auto pr-2">
        {tracks.map((track, index) => (
          <div
            key={track.id}
            className="flex items-center gap-3 p-2 hover:bg-spotify-light-gray rounded transition-colors"
          >
            <span className="text-spotify-text w-6 text-right text-sm flex-shrink-0">
              {index + 1}
            </span>
            {track.image ? (
              <img
                src={track.image}
                alt=""
                className="w-10 h-10 rounded flex-shrink-0"
              />
            ) : (
              <div className="w-10 h-10 rounded bg-spotify-light-gray flex items-center justify-center flex-shrink-0">
                <span className="text-spotify-text text-xs">♪</span>
              </div>
            )}
            <div className="flex-1 min-w-0">
              <p className="text-white truncate text-sm">{track.name}</p>
              <p className="text-spotify-text text-xs truncate">
                {track.artist}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
