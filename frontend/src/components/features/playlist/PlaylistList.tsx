import { useUser } from '../../../context/UserContext';
import { useGeneration } from '../../../context/GenerationContext';
import { PlaylistCard } from './PlaylistCard';
import { PlaylistListSkeleton } from '../../ui/Skeleton';

export function PlaylistList() {
  const { playlists, isLoading } = useUser();
  const { selectedPlaylistId, setSelectedPlaylist } = useGeneration();

  if (isLoading) {
    return <PlaylistListSkeleton />;
  }

  if (playlists.length === 0) {
    return (
      <div className="text-center py-8 text-spotify-text">
        <p>No public playlists found.</p>
        <p className="text-sm mt-2">
          Make some playlists public on Spotify to see them here.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-1 max-h-[300px] overflow-y-auto pr-2">
      {playlists.map((playlist) => (
        <PlaylistCard
          key={playlist.id}
          playlist={playlist}
          isSelected={selectedPlaylistId === playlist.id}
          onClick={() => setSelectedPlaylist(playlist.id, playlist.name)}
        />
      ))}
    </div>
  );
}
