import { useEffect, useRef } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useUser } from '../context/UserContext';
import { GenerationProvider, useGeneration } from '../context/GenerationContext';
import { ThreeColumnLayout } from '../components/layout';
import { ProfileCard } from '../components/features/profile';
import { GenerationTabs } from '../components/features/generation';
import { ResultCard } from '../components/features/generation';
import { PlaylistBrowseGuide } from '../components/features/playlist';
import { ProfileSkeleton, PlaylistListSkeleton, ResultSkeleton } from '../components/ui';

export function MainApp() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { profile, isLoading, username, setUsername } = useUser();
  const hasAttemptedLoad = useRef(false);

  // Load profile from URL param
  useEffect(() => {
    const userParam = searchParams.get('user');
    const decodedUserParam = userParam ? decodeURIComponent(userParam) : null;

    // Load if we have a user param and it's different from the current username
    if (decodedUserParam && decodedUserParam !== username && !isLoading) {
      setUsername(decodedUserParam);
    }
  }, [searchParams, username, isLoading, setUsername]);

  // Redirect to landing if no profile and no user param
  useEffect(() => {
    const userParam = searchParams.get('user');
    if (!isLoading && !profile && !userParam) {
      navigate('/');
    }
  }, [isLoading, profile, navigate, searchParams]);

  // Show loading state
  if (isLoading) {
    return (
      <ThreeColumnLayout
        left={<ProfileSkeleton />}
        middle={<PlaylistListSkeleton />}
        right={<ResultSkeleton />}
      />
    );
  }

  // Don't render if no profile (will redirect)
  if (!profile) {
    return null;
  }

  return (
    <GenerationProvider>
      <MainAppContent />
    </GenerationProvider>
  );
}

function MainAppContent() {
  const [searchParams] = useSearchParams();
  const { playlists } = useUser();
  const { playlistBrowseMode, selectedPlaylistId, setSelectedPlaylist } = useGeneration();
  const hasAutoSelected = useRef(false);

  // Auto-select playlist from query parameter
  useEffect(() => {
    const playlistParam = searchParams.get('playlist');

    // Only auto-select if:
    // - We have a playlist param
    // - Playlists are loaded
    // - No playlist is currently selected
    // - We haven't already auto-selected
    if (playlistParam && playlists.length > 0 && !selectedPlaylistId && !hasAutoSelected.current) {
      const playlistId = decodeURIComponent(playlistParam);
      const playlist = playlists.find(p => p.id === playlistId);

      if (playlist) {
        setSelectedPlaylist(
          playlist.id,
          playlist.name,
          `https://open.spotify.com/playlist/${playlist.id}`,
          playlist.images?.[0]?.url,
          'url'
        );
        hasAutoSelected.current = true;
      }
    }
  }, [searchParams, playlists, selectedPlaylistId, setSelectedPlaylist]);

  if (playlistBrowseMode) {
    return <PlaylistBrowseGuide />;
  }

  return (
    <ThreeColumnLayout
      left={<ProfileCard />}
      middle={<GenerationTabs />}
      right={<ResultCard />}
    />
  );
}
