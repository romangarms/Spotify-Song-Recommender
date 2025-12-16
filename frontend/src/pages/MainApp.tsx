import { useEffect, useRef } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useUser } from '../context/UserContext';
import { GenerationProvider } from '../context/GenerationContext';
import { ThreeColumnLayout } from '../components/layout';
import { ProfileCard } from '../components/features/profile';
import { GenerationTabs } from '../components/features/generation';
import { ResultCard } from '../components/features/generation';
import { ProfileSkeleton, PlaylistListSkeleton, ResultSkeleton } from '../components/ui';

export function MainApp() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { profile, isLoading, setUsername } = useUser();
  const hasAttemptedLoad = useRef(false);

  // Load profile from URL param on mount
  useEffect(() => {
    const userParam = searchParams.get('user');
    if (userParam && !profile && !isLoading && !hasAttemptedLoad.current) {
      hasAttemptedLoad.current = true;
      setUsername(decodeURIComponent(userParam));
    }
  }, [searchParams, profile, isLoading, setUsername]);

  // Redirect to landing if no profile and no user param
  useEffect(() => {
    const userParam = searchParams.get('user');
    if (!isLoading && !profile && !userParam) {
      navigate('/');
    }
  }, [isLoading, profile, navigate, searchParams]);

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
