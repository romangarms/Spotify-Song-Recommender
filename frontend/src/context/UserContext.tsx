import type { ReactNode } from 'react';
import {
  createContext,
  useContext,
  useState,
  useCallback,
} from 'react';
import type { SpotifyProfile, Playlist } from '../types';
import { api } from '../api/client';

interface UserContextType {
  profile: SpotifyProfile | null;
  playlists: Playlist[];
  isLoading: boolean;
  error: string | null;
  username: string | null;
  setUsername: (username: string) => Promise<void>;
  refreshPlaylists: () => Promise<void>;
  clearUser: () => void;
}

const UserContext = createContext<UserContextType | undefined>(undefined);

interface UserProviderProps {
  children: ReactNode;
}

export function UserProvider({ children }: UserProviderProps) {
  const [profile, setProfile] = useState<SpotifyProfile | null>(null);
  const [playlists, setPlaylists] = useState<Playlist[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [username, setUsernameState] = useState<string | null>(null);

  const setUsername = useCallback(async (username: string) => {
    setIsLoading(true);
    setError(null);
    setUsernameState(username);

    try {
      // Fetch profile and playlists in parallel
      const [profileData, playlistsData] = await Promise.all([
        api.getProfile(username),
        api.getPlaylists(username),
      ]);

      setProfile(profileData);
      setPlaylists(playlistsData.playlists);
    } catch (e) {
      const errorMessage =
        e instanceof Error ? e.message : 'Failed to load profile';
      setError(errorMessage);
      setUsernameState(null);
      throw e;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const refreshPlaylists = useCallback(async () => {
    if (!username) return;

    setIsLoading(true);
    setError(null);

    try {
      const playlistsData = await api.getPlaylists(username);
      setPlaylists(playlistsData.playlists);
    } catch (e) {
      const errorMessage =
        e instanceof Error ? e.message : 'Failed to load playlists';
      setError(errorMessage);
      throw e;
    } finally {
      setIsLoading(false);
    }
  }, [username]);

  const clearUser = useCallback(() => {
    setProfile(null);
    setPlaylists([]);
    setError(null);
    setUsernameState(null);
  }, []);

  return (
    <UserContext.Provider
      value={{
        profile,
        playlists,
        isLoading,
        error,
        username,
        setUsername,
        refreshPlaylists,
        clearUser,
      }}
    >
      {children}
    </UserContext.Provider>
  );
}

export function useUser() {
  const context = useContext(UserContext);
  if (context === undefined) {
    throw new Error('useUser must be used within a UserProvider');
  }
  return context;
}
