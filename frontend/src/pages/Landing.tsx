import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui';

const STEPS = [
  'Add songs that capture the sound you want — search for them, or paste Spotify song links straight from the app',
  'An LLM reads those songs and works out the taste behind them',
  'It picks 15 recommendations that fit',
  'A new Spotify playlist is created and handed back to you',
];

export function Landing() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-5">
      <div className="max-w-[600px] w-full text-center">
        <div className="mb-8">
          <h1 className="text-5xl font-black text-white mb-4">
            Spotify Song Recommender
          </h1>
          <p className="text-xl text-spotify-text leading-relaxed">
            Pick a few songs you love and get a fresh playlist built around
            them, powered by the Logic API.
          </p>
        </div>

        <Button
          size="lg"
          className="w-full mb-8"
          onClick={() => navigate('/app')}
        >
          Get Started
        </Button>

        <div className="bg-spotify-gray rounded-2xl p-6 text-left">
          <h2 className="text-lg font-semibold text-white mb-4">How it works:</h2>
          <ol className="space-y-3 text-spotify-text">
            {STEPS.map((step, index) => (
              <li key={step} className="flex items-start gap-3">
                <span className="text-spotify-green font-semibold min-w-6">
                  {index + 1}.
                </span>
                <span>{step}</span>
              </li>
            ))}
          </ol>
        </div>

        <p className="text-gray-600 text-sm mt-8">
          No login required • Your playlist is created for you to keep
        </p>
      </div>
    </div>
  );
}
