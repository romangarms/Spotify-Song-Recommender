import { useUser } from '../../context/UserContext';

export function Header() {
  const { profile } = useUser();

  return (
    <header className="bg-spotify-dark border-b border-gray-800 p-4">
      <div className="container mx-auto flex items-center justify-between">
        <h1 className="text-xl font-bold text-white">
          Spotify Song Recommender
        </h1>

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
