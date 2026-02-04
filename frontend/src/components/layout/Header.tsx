import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useUser } from '../../context/UserContext';
import { Button } from '../ui';

export function Header() {
  const { profile } = useUser();
  const navigate = useNavigate();
  const location = useLocation();

  const isOnMainApp = location.pathname === '/app';

  return (
    <header className="bg-spotify-dark border-b border-gray-800 p-4">
      <div className="container mx-auto flex items-center justify-between">
        <div className="flex items-center gap-4">
          {/* Back Button - only show on app page */}
          {isOnMainApp && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate('/')}
              className="text-spotify-text hover:text-white -ml-2"
            >
              <span className="mr-1">←</span>
              Back
            </Button>
          )}

          {/* Logo */}
          <Link to="/">
            <h1 className="text-xl font-bold text-white cursor-pointer hover:text-spotify-green transition-colors">
              Spotify Song Recommender
            </h1>
          </Link>
        </div>

        {/* Show profile in header on smaller screens */}
        <div className="flex items-center gap-4 lg:hidden">
          {profile && (
            <>
              <span className="text-white hidden sm:inline text-sm">
                {profile.display_name}
              </span>
              {profile.images?.[0] && (
                <img
                  src={profile.images[0].url}
                  alt={profile.display_name}
                  className="w-8 h-8 rounded-full object-cover"
                />
              )}
            </>
          )}
        </div>
      </div>
    </header>
  );
}
