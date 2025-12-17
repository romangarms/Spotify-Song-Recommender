import { useState } from 'react';
import { Tabs, Button } from '../../ui';
import { PlaylistList, PlaylistUrlInput } from '../playlist';
import { TextInput } from './TextInput';
import { useGeneration } from '../../../context/GenerationContext';

export function GenerationTabs() {
  const [activeTab, setActiveTab] = useState('playlist');
  const {
    state,
    selectedPlaylistId,
    textDescription,
    generateFromPlaylist,
    generateFromText,
  } = useGeneration();

  const isLoading = state.status === 'loading';

  const handleGenerate = () => {
    if (activeTab === 'playlist') {
      generateFromPlaylist();
    } else {
      generateFromText();
    }
  };

  const canGenerate =
    activeTab === 'playlist' ? !!selectedPlaylistId : !!textDescription.trim();

  return (
    <div className="space-y-4">
      <Tabs
        tabs={[
          { id: 'playlist', label: 'From Playlist' },
          { id: 'text', label: 'From Text' },
        ]}
        activeTab={activeTab}
        onChange={setActiveTab}
      />

      <div className="min-h-[400px]">
        {activeTab === 'playlist' ? (
          <div className="space-y-4">
            {/* URL Input Section */}
            <div>
              <h3 className="text-white font-semibold mb-2">
                Paste any playlist URL:
              </h3>
              <p className="text-spotify-text text-sm mb-2">
                Use any public playlist as inspiration (even from other users)
              </p>
              <PlaylistUrlInput />
            </div>

            {/* Divider */}
            <div className="flex items-center gap-4">
              <div className="flex-1 h-px bg-gray-700" />
              <span className="text-spotify-text text-sm">OR</span>
              <div className="flex-1 h-px bg-gray-700" />
            </div>

            {/* Playlist List */}
            <div>
              <h3 className="text-white font-semibold mb-2">
                Choose from your playlists:
              </h3>
              <PlaylistList />
            </div>
          </div>
        ) : (
          <TextInput />
        )}
      </div>

      {/* Generate Button */}
      <Button
        onClick={handleGenerate}
        disabled={!canGenerate || isLoading}
        isLoading={isLoading}
        className="w-full"
        size="lg"
      >
        Generate New Playlist
      </Button>
    </div>
  );
}
