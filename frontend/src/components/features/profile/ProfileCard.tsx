import { useNavigate } from 'react-router-dom';
import { useUser } from '../../../context/UserContext';
import { useLocalStorage } from '../../../hooks';
import { Button } from '../../ui';
import { ProfileSkeleton } from '../../ui/Skeleton';

interface UserHistoryItem {
  username: string;
  displayName: string;
}

const USER_HISTORY_KEY = 'spotify_user_history_v1';
const MAX_DISPLAY = 5;

export function ProfileCard() {
  const navigate = useNavigate();
  const { profile, isLoading, clearUser } = useUser();
  const [recentUsers] = useLocalStorage<UserHistoryItem[]>(USER_HISTORY_KEY, []);

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

  // Filter out current user from recent users list
  const otherRecentUsers = recentUsers.filter(user => user.username !== profile.id);

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

      {/* Recent Users */}
      {otherRecentUsers.length > 0 && (
        <div className="mt-4 pt-4 border-t border-gray-700 w-full">
          <p className="text-xs text-gray-500 mb-2 uppercase tracking-wide">Recent Users</p>
          <div className="space-y-1">
            {otherRecentUsers.slice(0, MAX_DISPLAY).map((user, index) => (
              <button
                key={index}
                onClick={() => navigate(`/app?user=${encodeURIComponent(user.username)}`)}
                className="w-full text-left px-2 py-1.5 text-sm text-spotify-text hover:text-white hover:bg-spotify-light-gray rounded transition-colors flex items-center gap-2"
              >
                <span className="text-spotify-green">→</span>
                <span className="truncate">{user.displayName}</span>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
