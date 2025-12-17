/**
 * TypeScript type definitions for the Spotify Song Recommender
 */

export interface SpotifyImage {
  url: string;
  height?: number;
  width?: number;
}

export interface SpotifyProfile {
  id: string;
  display_name: string;
  images: SpotifyImage[];
  external_urls?: {
    spotify?: string;
  };
}

export interface Playlist {
  id: string;
  name: string;
  images: SpotifyImage[];
  tracks_total: number;
}

export interface Track {
  id: string;
  name: string;
  artist: string;
  album: string;
  image: string | null;
}

export interface GeneratedPlaylist {
  playlist_id: string;
  playlist_url: string;
  title: string;
  description: string;
  tracks: Track[];
  not_found?: string[];
}

export interface PlaylistValidation {
  playlist_id: string;
  playlist_name: string;
  tracks_total: number;
  images: SpotifyImage[];
}

export type GenerationStatus = 'idle' | 'loading' | 'success' | 'error';

export interface GenerationState {
  status: GenerationStatus;
  result: GeneratedPlaylist | null;
  error: string | null;
}

export interface ApiError {
  error: string;
  message: string;
}
