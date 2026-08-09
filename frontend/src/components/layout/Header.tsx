import { Link, useNavigate, useLocation } from 'react-router-dom';
import { Button } from '../ui';

export function Header() {
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
      </div>
    </header>
  );
}
