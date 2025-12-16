import { useGeneration } from '../../../context/GenerationContext';

export function TextInput() {
  const { textDescription, setTextDescription } = useGeneration();

  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-white font-semibold mb-2">
          Describe your ideal playlist:
        </h3>
        <p className="text-spotify-text text-sm mb-4">
          Tell us the vibe, mood, genre, or any specific requirements for your
          playlist.
        </p>
      </div>

      <textarea
        value={textDescription}
        onChange={(e) => setTextDescription(e.target.value)}
        placeholder="Example: Summer vibes with modern indie and alternative rock. Upbeat but not too energetic, perfect for a road trip or beach day. Include some lesser-known artists alongside popular ones."
        className="w-full h-48 px-4 py-3 bg-spotify-light-gray text-white rounded-lg border border-gray-600 placeholder-spotify-text focus:border-spotify-green focus:outline-none transition-colors resize-none"
      />

      <div className="text-spotify-text text-sm">
        <p className="font-medium mb-2">Tips for better results:</p>
        <ul className="list-disc list-inside space-y-1">
          <li>Be specific about genres and moods</li>
          <li>Mention artists you like for reference</li>
          <li>Describe the activity or setting</li>
          <li>Include any specific requirements (e.g., "no lyrics")</li>
        </ul>
      </div>
    </div>
  );
}
