import type { ReactNode } from 'react';
import { GuideStep } from './GuideStep';

interface Step {
  title: string;
  description: string;
}

interface SpotifyGuideLayoutProps {
  title: string;
  subtitle: string;
  steps: Step[];
  tip?: string;
  onBack: () => void;
  children: ReactNode;
}

export function SpotifyGuideLayout({
  title,
  subtitle,
  steps,
  tip,
  onBack,
  children,
}: SpotifyGuideLayoutProps) {
  return (
    <div className="min-h-screen flex flex-col p-8 w-1/2">
      <button
        type="button"
        onClick={onBack}
        className="text-spotify-text hover:text-white mb-6 self-start flex items-center gap-2"
      >
        &larr; Back
      </button>

      <div className="flex-1 flex flex-col justify-center max-w-lg">
        <h1 className="text-3xl font-bold text-white mb-2">{title}</h1>
        <p className="text-spotify-text mb-8">{subtitle}</p>

        <ol className="space-y-6 mb-10">
          {steps.map((step, index) => (
            <GuideStep
              key={index}
              number={index + 1}
              title={step.title}
              description={step.description}
            />
          ))}
        </ol>

        {tip && (
          <div className="bg-spotify-gray rounded-lg p-4 mb-6">
            <p className="text-spotify-text text-sm">
              <span className="text-white font-medium">Tip:</span> {tip}
            </p>
          </div>
        )}

        {children}
      </div>
    </div>
  );
}
