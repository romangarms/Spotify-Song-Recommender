import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useUser } from '../context/UserContext';
import { GenerationProvider } from '../context/GenerationContext';
import { ThreeColumnLayout } from '../components/layout';
import { ProfileCard } from '../components/features/profile';
import { GenerationTabs } from '../components/features/generation';
import { ResultCard } from '../components/features/generation';
import { ProfileSkeleton, PlaylistListSkeleton, ResultSkeleton } from '../components/ui';

export function MainApp() {
  const navigate = useNavigate();
  const { profile, isLoading } = useUser();

  // Redirect to landing if no profile
  useEffect(() => {
    if (!isLoading && !profile) {
      navigate('/');
    }
  }, [isLoading, profile, navigate]);

  // Show loading state
  if (isLoading) {
    return (
      <ThreeColumnLayout
        left={<ProfileSkeleton />}
        middle={<PlaylistListSkeleton />}
        right={<ResultSkeleton />}
      />
    );
  }

  // Don't render if no profile (will redirect)
  if (!profile) {
    return null;
  }

  return (
    <GenerationProvider>
      <ThreeColumnLayout
        left={<ProfileCard />}
        middle={<GenerationTabs />}
        right={<ResultCard />}
      />
    </GenerationProvider>
  );
}
