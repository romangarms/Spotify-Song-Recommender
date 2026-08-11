import type { ReactNode } from 'react';
import {
  createContext,
  useContext,
  useState,
  useCallback,
} from 'react';
import type { GenerationState, GeneratedPlaylist, SeedTrack } from '../types';
import { api } from '../api/client';

interface GenerationContextType {
  state: GenerationState;
  selectedPlaylistId: string | null;
  selectedPlaylistName: string | null;
  selectedPlaylistUrl: string | null;
  selectedPlaylistImage: string | null;
  selectionSource: 'url' | 'list' | null;
  textDescription: string;
  seedTracks: SeedTrack[];
  setSelectedPlaylist: (id: string | null, name?: string | null, url?: string | null, imageUrl?: string | null, source?: 'url' | 'list' | null) => void;
  setTextDescription: (text: string) => void;
  addSeedTracks: (tracks: SeedTrack[]) => void;
  removeSeedTrack: (id: string) => void;
  clearSeedTracks: () => void;
  generateFromPlaylist: () => Promise<void>;
  generateFromText: () => Promise<void>;
  generateFromTracks: () => Promise<void>;
  reset: () => void;
}

const GenerationContext = createContext<GenerationContextType | undefined>(
  undefined
);

interface GenerationProviderProps {
  children: ReactNode;
}

const initialState: GenerationState = {
  status: 'idle',
  result: null,
  error: null,
};

// Rate limit errors arrive as "message|||retryAfter"; the message already
// names the wait, so the suffix is dropped.
function toErrorMessage(e: unknown): string {
  if (!(e instanceof Error)) {
    return 'Failed to generate playlist';
  }
  return e.message.split('|||')[0];
}

export function GenerationProvider({ children }: GenerationProviderProps) {
  const [state, setState] = useState<GenerationState>(initialState);
  const [selectedPlaylistId, setSelectedPlaylistId] = useState<string | null>(
    null
  );
  const [selectedPlaylistName, setSelectedPlaylistName] = useState<
    string | null
  >(null);
  const [selectedPlaylistUrl, setSelectedPlaylistUrl] = useState<string | null>(
    null
  );
  const [selectedPlaylistImage, setSelectedPlaylistImage] = useState<string | null>(
    null
  );
  const [selectionSource, setSelectionSource] = useState<'url' | 'list' | null>(null);
  const [textDescription, setTextDescriptionState] = useState('');
  const [seedTracks, setSeedTracks] = useState<SeedTrack[]>([]);

  const addSeedTracks = useCallback((tracks: SeedTrack[]) => {
    setSeedTracks((current) => {
      const seen = new Set(current.map((t) => t.id));
      return [...current, ...tracks.filter((t) => !seen.has(t.id))];
    });
  }, []);

  const removeSeedTrack = useCallback((id: string) => {
    setSeedTracks((current) => current.filter((t) => t.id !== id));
  }, []);

  const clearSeedTracks = useCallback(() => setSeedTracks([]), []);

  const setSelectedPlaylist = useCallback(
    (id: string | null, name?: string | null, url?: string | null, imageUrl?: string | null, source?: 'url' | 'list' | null) => {
      setSelectedPlaylistId(id);
      setSelectedPlaylistName(name ?? null);
      setSelectedPlaylistUrl(url ?? null);
      setSelectedPlaylistImage(imageUrl ?? null);
      setSelectionSource(id ? (source ?? 'list') : null);
    },
    []
  );

  const setTextDescription = useCallback((text: string) => {
    setTextDescriptionState(text);
  }, []);

  const generateFromPlaylist = useCallback(async () => {
    if (!selectedPlaylistId) {
      setState({
        status: 'error',
        result: null,
        error: 'Please select a playlist first',
      });
      return;
    }

    setState({ status: 'loading', result: null, error: null });

    try {
      const result: GeneratedPlaylist =
        await api.generateFromPlaylist(selectedPlaylistId);
      setState({ status: 'success', result, error: null });
    } catch (e) {
      setState({ status: 'error', result: null, error: toErrorMessage(e) });
    }
  }, [selectedPlaylistId]);

  const generateFromText = useCallback(async () => {
    if (!textDescription.trim()) {
      setState({
        status: 'error',
        result: null,
        error: 'Please enter a description first',
      });
      return;
    }

    setState({ status: 'loading', result: null, error: null });

    try {
      const result: GeneratedPlaylist =
        await api.generateFromText(textDescription);
      setState({ status: 'success', result, error: null });
    } catch (e) {
      setState({ status: 'error', result: null, error: toErrorMessage(e) });
    }
  }, [textDescription]);

  const generateFromTracks = useCallback(async () => {
    if (seedTracks.length === 0) {
      setState({
        status: 'error',
        result: null,
        error: 'Please add at least one song first',
      });
      return;
    }

    setState({ status: 'loading', result: null, error: null });

    try {
      const result: GeneratedPlaylist = await api.generateFromTracks(
        seedTracks.map((t) => t.id)
      );
      setState({ status: 'success', result, error: null });
    } catch (e) {
      setState({ status: 'error', result: null, error: toErrorMessage(e) });
    }
  }, [seedTracks]);

  const reset = useCallback(() => {
    setState(initialState);
    setSelectedPlaylistId(null);
    setSelectedPlaylistName(null);
    setSelectedPlaylistUrl(null);
    setSelectedPlaylistImage(null);
    setSelectionSource(null);
    setTextDescriptionState('');
    setSeedTracks([]);
  }, []);

  return (
    <GenerationContext.Provider
      value={{
        state,
        selectedPlaylistId,
        selectedPlaylistName,
        selectedPlaylistUrl,
        selectedPlaylistImage,
        selectionSource,
        textDescription,
        seedTracks,
        setSelectedPlaylist,
        setTextDescription,
        addSeedTracks,
        removeSeedTrack,
        clearSeedTracks,
        generateFromPlaylist,
        generateFromText,
        generateFromTracks,
        reset,
      }}
    >
      {children}
    </GenerationContext.Provider>
  );
}

export function useGeneration() {
  const context = useContext(GenerationContext);
  if (context === undefined) {
    throw new Error('useGeneration must be used within a GenerationProvider');
  }
  return context;
}
