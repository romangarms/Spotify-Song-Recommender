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
    <div className="h-screen flex flex-col bg-spotify-black overflow-hidden">
      <Header />
      <div className="flex-1 container mx-auto p-4 overflow-hidden">
        {/* Mobile Layout - Single column */}
        <div className="h-full flex flex-col gap-4 md:hidden">
          <Card className="flex-1 flex flex-col overflow-hidden">{middle}</Card>
          <Card className="flex-1 flex flex-col overflow-hidden">{right}</Card>
        </div>

        {/* Portrait/Tablet Layout (md) - Profile+Output stacked left, Playlist right */}
        <div className="hidden md:grid lg:hidden h-full grid-cols-2 gap-4">
          <div className="flex flex-col gap-4 h-full min-h-0">
            <Card className="flex-shrink-0">{left}</Card>
            <Card className="flex-1 flex flex-col overflow-hidden min-h-0">{right}</Card>
          </div>
          <Card className="flex flex-col overflow-hidden">{middle}</Card>
        </div>

        {/* Widescreen Layout (lg+) - 3 columns */}
        <div className="hidden lg:grid h-full grid-cols-[280px_1fr_1fr] gap-4">
          <div className="h-fit">
            <Card>{left}</Card>
          </div>
          <Card className="flex flex-col overflow-hidden">{middle}</Card>
          <Card className="flex flex-col overflow-hidden">{right}</Card>
        </div>
      </div>
    </div>
  );
}
