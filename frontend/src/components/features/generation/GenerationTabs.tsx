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
    <div className="flex flex-col h-full min-h-0">
      <Tabs
        tabs={[
          { id: 'playlist', label: 'From Playlist' },
          { id: 'text', label: 'From Text' },
        ]}
        activeTab={activeTab}
        onChange={setActiveTab}
      />

      <div className="flex-1 min-h-0 overflow-y-auto mt-4">
        {activeTab === 'playlist' ? (
          <div className="flex flex-col h-full">
            {/* URL Input Section */}
            <div className="flex-shrink-0">
              <h3 className="text-white font-semibold mb-2">
                Paste any playlist URL:
              </h3>
              <p className="text-spotify-text text-sm mb-2">
                Use any public playlist as inspiration (even from other users)
              </p>
              <PlaylistUrlInput />
            </div>

            {/* Divider */}
            <div className="flex items-center gap-4 my-4 flex-shrink-0">
              <div className="flex-1 h-px bg-gray-700" />
              <span className="text-spotify-text text-sm">OR</span>
              <div className="flex-1 h-px bg-gray-700" />
            </div>

            {/* Playlist List */}
            <div className="flex-1 min-h-0 flex flex-col">
              <h3 className="text-white font-semibold mb-2 flex-shrink-0">
                Choose from your playlists:
              </h3>
              <div className="flex-1 min-h-0">
                <PlaylistList />
              </div>
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
        className="w-full mt-4 flex-shrink-0"
        size="lg"
      >
        Generate New Playlist
      </Button>
    </div>
  );
}
