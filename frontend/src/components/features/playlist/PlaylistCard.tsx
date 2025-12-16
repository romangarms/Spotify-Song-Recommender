import type { Playlist } from '../../../types';

interface PlaylistCardProps {
  playlist: Playlist;
  isSelected: boolean;
  onClick: () => void;
}

export function PlaylistCard({
  playlist,
  isSelected,
  onClick,
}: PlaylistCardProps) {
  const imageUrl = playlist.images?.[0]?.url;

  return (
    <button
      onClick={onClick}
      className={`w-full flex items-center gap-3 p-2 rounded-lg transition-colors text-left ${
        isSelected
          ? 'bg-spotify-light-gray border-l-4 border-spotify-green'
          : 'hover:bg-spotify-light-gray/50'
      }`}
    >
      {imageUrl ? (
        <img
          src={imageUrl}
          alt={playlist.name}
          className="w-12 h-12 rounded object-cover flex-shrink-0"
        />
      ) : (
        <div className="w-12 h-12 rounded bg-spotify-light-gray flex items-center justify-center flex-shrink-0">
          <span className="text-spotify-text text-xs">♪</span>
        </div>
      )}

      <div className="flex-1 min-w-0">
        <p className="text-white font-medium truncate">{playlist.name}</p>
        <p className="text-spotify-text text-sm">
          {playlist.tracks_total} tracks
        </p>
      </div>

      {isSelected && (
        <span className="text-spotify-green text-lg flex-shrink-0">✓</span>
      )}
    </button>
  );
}
