import { useState } from 'react';
import { Tabs, Button } from '../../ui';
import { TextInput } from './TextInput';
import { SongSeedInput } from './SongSeedInput';
import { useGeneration } from '../../../context/GenerationContext';

export function GenerationTabs() {
  const [activeTab, setActiveTab] = useState('songs');
  const {
    state,
    seedTracks,
    textDescription,
    generateFromTracks,
    generateFromText,
  } = useGeneration();

  const isLoading = state.status === 'loading';

  const handleGenerate = () => {
    if (activeTab === 'songs') {
      generateFromTracks();
    } else {
      generateFromText();
    }
  };

  const canGenerate =
    activeTab === 'songs' ? seedTracks.length > 0 : !!textDescription.trim();

  return (
    <div className="flex flex-col h-full min-h-0">
      <Tabs
        tabs={[
          { id: 'songs', label: 'From Songs' },
          { id: 'text', label: 'From Text' },
        ]}
        activeTab={activeTab}
        onChange={setActiveTab}
      />

      <div className="flex-1 min-h-0 overflow-y-auto mt-4">
        {activeTab === 'songs' ? <SongSeedInput /> : <TextInput />}
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
