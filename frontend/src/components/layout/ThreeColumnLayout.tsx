import type { ReactNode } from 'react';
import { Header } from './Header';
import { Card } from '../ui';

interface ThreeColumnLayoutProps {
  left: ReactNode;
  middle: ReactNode;
  right: ReactNode;
}

export function ThreeColumnLayout({
  left,
  middle,
  right,
}: ThreeColumnLayoutProps) {
  return (
    <div className="min-h-screen bg-spotify-black">
      <Header />
      <div className="container mx-auto p-4">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-[280px_1fr_1fr] gap-4">
          {/* Left Column - Profile (hidden on mobile, shown on tablet+) */}
          <div className="hidden md:block lg:sticky lg:top-4 lg:h-fit">
            <Card>{left}</Card>
          </div>

          {/* Middle Column - Input Selection */}
          <Card className="md:col-span-1">{middle}</Card>

          {/* Right Column - Generated Output */}
          <Card className="md:col-span-1">{right}</Card>
        </div>
      </div>
    </div>
  );
}
