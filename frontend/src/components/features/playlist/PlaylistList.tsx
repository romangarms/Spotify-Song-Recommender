import { useRef, useEffect } from 'react';
import { useUser } from '../../../context/UserContext';
import { useGeneration } from '../../../context/GenerationContext';
import { PlaylistCard } from './PlaylistCard';
import { PlaylistListSkeleton } from '../../ui/Skeleton';

export function PlaylistList() {
  const { playlists, isLoading } = useUser();
  const { selectedPlaylistId, setSelectedPlaylist, selectionSource } = useGeneration();
  const selectedRef = useRef<HTMLDivElement>(null);
  const hasScrolled = useRef(false);

  // Auto-scroll to selected playlist when it's selected from URL
  useEffect(() => {
    if (selectedPlaylistId && selectionSource === 'url' && !hasScrolled.current && selectedRef.current) {
      selectedRef.current.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      hasScrolled.current = true;
    }
    // Reset scroll flag when selection changes
    if (!selectedPlaylistId) {
      hasScrolled.current = false;
    }
  }, [selectedPlaylistId, selectionSource]);

  if (isLoading) {
    return <PlaylistListSkeleton />;
  }

  if (playlists.length === 0) {
    return (
      <div className="py-8 text-spotify-text max-w-sm mx-auto">
        <p className="text-center">No public playlists found.</p>
        <p className="text-sm mt-3 text-left">
          To appear here, playlists must be both public AND added to your Spotify profile.
        </p>
        <p className="text-sm mt-2 text-left">
          In Spotify: right-click a playlist → Make Public, then right-click the playlist again → Add to Profile.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-1 h-full overflow-y-auto pr-2">
      {playlists.map((playlist) => (
        <div
          key={playlist.id}
          ref={selectedPlaylistId === playlist.id ? selectedRef : null}
        >
          <PlaylistCard
            playlist={playlist}
            isSelected={selectedPlaylistId === playlist.id}
            onClick={() => setSelectedPlaylist(playlist.id, playlist.name, undefined, undefined, 'list')}
          />
        </div>
      ))}
    </div>
  );
}
