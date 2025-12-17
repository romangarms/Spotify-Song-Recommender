import type { ReactNode } from 'react';
import {
  createContext,
  useContext,
  useState,
  useCallback,
} from 'react';
import type { GenerationState, GeneratedPlaylist } from '../types';
import { api } from '../api/client';

interface GenerationContextType {
  state: GenerationState;
  selectedPlaylistId: string | null;
  selectedPlaylistName: string | null;
  textDescription: string;
  setSelectedPlaylist: (id: string | null, name?: string | null) => void;
  setTextDescription: (text: string) => void;
  generateFromPlaylist: () => Promise<void>;
  generateFromText: () => Promise<void>;
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

export function GenerationProvider({ children }: GenerationProviderProps) {
  const [state, setState] = useState<GenerationState>(initialState);
  const [selectedPlaylistId, setSelectedPlaylistId] = useState<string | null>(
    null
  );
  const [selectedPlaylistName, setSelectedPlaylistName] = useState<
    string | null
  >(null);
  const [textDescription, setTextDescriptionState] = useState('');

  const setSelectedPlaylist = useCallback(
    (id: string | null, name?: string | null) => {
      setSelectedPlaylistId(id);
      setSelectedPlaylistName(name ?? null);
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
      const errorMessage =
        e instanceof Error ? e.message : 'Failed to generate playlist';
      setState({ status: 'error', result: null, error: errorMessage });
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
      const errorMessage =
        e instanceof Error ? e.message : 'Failed to generate playlist';
      setState({ status: 'error', result: null, error: errorMessage });
    }
  }, [textDescription]);

  const reset = useCallback(() => {
    setState(initialState);
    setSelectedPlaylistId(null);
    setSelectedPlaylistName(null);
    setTextDescriptionState('');
  }, []);

  return (
    <GenerationContext.Provider
      value={{
        state,
        selectedPlaylistId,
        selectedPlaylistName,
        textDescription,
        setSelectedPlaylist,
        setTextDescription,
        generateFromPlaylist,
        generateFromText,
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
