/**
 * API client for communicating with the Flask backend
 */

import type {
  SpotifyProfile,
  Playlist,
  Track,
  GeneratedPlaylist,
  PlaylistValidation,
  ApiError,
  PlaylistOwnerResponse,
  PlaylistSearchResponse,
} from '../types';

const API_BASE = '/api';

class ApiClient {
  private async fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${API_BASE}${url}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    const data = await response.json();

    if (!response.ok) {
      const error = data as ApiError;
      throw new Error(error.message || error.error || 'Request failed');
    }

    return data;
  }

  /**
   * Fetch a user's public profile
   */
  async getProfile(username: string): Promise<SpotifyProfile> {
    return this.fetchJson<SpotifyProfile>(`/profile/${encodeURIComponent(username)}`);
  }

  /**
   * Fetch a user's public playlists
   */
  async getPlaylists(username: string): Promise<{ playlists: Playlist[] }> {
    return this.fetchJson<{ playlists: Playlist[] }>(`/profile/${encodeURIComponent(username)}/playlists`);
  }

  /**
   * Get tracks from a playlist
   */
  async getPlaylistTracks(playlistId: string): Promise<{ name: string; tracks: Track[] }> {
    return this.fetchJson<{ name: string; tracks: Track[] }>(`/playlist/${playlistId}/tracks`);
  }

  /**
   * Validate a playlist URL
   */
  async validatePlaylistUrl(playlistUrl: string): Promise<PlaylistValidation> {
    return this.fetchJson<PlaylistValidation>('/playlist/validate', {
      method: 'POST',
      body: JSON.stringify({ playlist_url: playlistUrl }),
    });
  }

  /**
   * Generate a playlist from an existing playlist
   */
  async generateFromPlaylist(playlistId: string): Promise<GeneratedPlaylist> {
    return this.fetchJson<GeneratedPlaylist>('/generate/from-playlist', {
      method: 'POST',
      body: JSON.stringify({ playlist_id: playlistId }),
    });
  }

  /**
   * Generate a playlist from a text description
   */
  async generateFromText(description: string): Promise<GeneratedPlaylist> {
    return this.fetchJson<GeneratedPlaylist>('/generate/from-text', {
      method: 'POST',
      body: JSON.stringify({ description }),
    });
  }

  /**
   * Get playlist owner username from playlist URL
   */
  async getPlaylistOwner(playlistUrl: string): Promise<PlaylistOwnerResponse> {
    return this.fetchJson<PlaylistOwnerResponse>('/playlist/owner', {
      method: 'POST',
      body: JSON.stringify({ playlist_url: playlistUrl }),
    });
  }

  /**
   * Search for public playlists
   */
  async searchPlaylists(query: string, limit: number = 10): Promise<PlaylistSearchResponse> {
    return this.fetchJson<PlaylistSearchResponse>(
      `/search/playlists?q=${encodeURIComponent(query)}&limit=${limit}`
    );
  }

  /**
   * Health check
   */
  async healthCheck(): Promise<{ status: string }> {
    return this.fetchJson<{ status: string }>('/health');
  }
}

export const api = new ApiClient();
