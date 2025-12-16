import { useNavigate } from 'react-router-dom';
import { useUser } from '../../../context/UserContext';
import { Button } from '../../ui';
import { ProfileSkeleton } from '../../ui/Skeleton';

export function ProfileCard() {
  const navigate = useNavigate();
  const { profile, isLoading, clearUser } = useUser();

  if (isLoading) {
    return <ProfileSkeleton />;
  }

  if (!profile) {
    return null;
  }

  const avatarUrl = profile.images?.[0]?.url;

  const handleSignOut = () => {
    clearUser();
    navigate('/');
  };

  return (
    <div className="flex flex-col items-center text-center">
      {avatarUrl ? (
        <img
          src={avatarUrl}
          alt={profile.display_name}
          className="w-32 h-32 rounded-full object-cover mb-4"
        />
      ) : (
        <div className="w-32 h-32 rounded-full bg-spotify-light-gray mb-4 flex items-center justify-center">
          <span className="text-4xl text-spotify-text">
            {profile.display_name[0].toUpperCase()}
          </span>
        </div>
      )}

      <h2 className="text-xl font-bold text-white mb-2">
        {profile.display_name}
      </h2>

      <a
        href={`https://open.spotify.com/user/${profile.id}`}
        target="_blank"
        rel="noopener noreferrer"
        className="text-spotify-text hover:text-spotify-green text-sm mb-4 transition-colors"
      >
        View on Spotify ↗
      </a>

      <Button variant="ghost" size="sm" onClick={handleSignOut}>
        Change User
      </Button>
    </div>
  );
}
