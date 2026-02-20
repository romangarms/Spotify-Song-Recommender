# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Full-stack web application for generating personalized Spotify playlists using AI. Users can generate playlists without OAuth login by pasting public Spotify playlist URLs or describing their ideal playlist in text. A "system account" creates playlists on behalf of users.

## System Account Architecture (No User OAuth)

Spotify's 2025+ OAuth requirements make public app approval difficult for small projects. This app bypasses end-user OAuth entirely using a "system account" pattern.

### How It Works
1. Admin authenticates once via `/api/admin/spotify-setup?key=ADMIN_SECRET`
2. OAuth callback returns a long-lived refresh token stored in `SPOTIFY_SYSTEM_REFRESH_TOKEN`
3. All API calls use this token—users never see an OAuth screen
4. Token refresh handled automatically in `backend/services/system_account.py` with thread-safe caching

### Spotify APIs Available

**Read Operations (Public Data - No User Auth Needed):**
| Endpoint | Purpose | Limitation |
|----------|---------|------------|
| `GET /v1/users/{user_id}` | Public user profile | Display name, images only |
| `GET /v1/users/{user_id}/playlists` | User's playlists | Filtered to `public=true` only |
| `GET /v1/playlists/{playlist_id}` | Playlist tracks | Public playlists only (404 if private) |
| `GET /v1/search` | Search tracks/playlists | Public search index |

**Write Operations (Via System Account):**
| Endpoint | Purpose |
|----------|---------|
| `POST /v1/users/{user_id}/playlists` | Create playlist on system account |
| `PUT /v1/playlists/{playlist_id}` | Update playlist name/description |
| `POST /v1/playlists/{playlist_id}/tracks` | Add tracks (max 100 per request) |

### Data Limitations

**Can Access:** Public user profiles, public playlists and their tracks, Spotify's public search index

**Cannot Access:** Private playlists, user's "Liked Songs" or library, listening history, private user info (email, account type), saved tracks or followed artists

### OAuth Scopes (Admin Setup Only)
- `playlist-modify-public` - Create/edit public playlists on system account
- `user-read-private` - Get system account's user ID for playlist creation

### Key Files
- `backend/services/system_account.py` - Token management, public data access, playlist creation
- `backend/blueprints/admin.py` - One-time OAuth setup flow
- `backend/services/spotify.py` - Track search & playlist population

## Development Commands

```bash
npm run dev               # Build frontend + concurrent dev (backend + frontend watch)
npm run dev:backend      # Backend only (port 5001)
npm run watch:frontend   # Frontend auto-rebuild (Vite watch mode)
npm run build:frontend   # Production frontend build
```

**Initial Setup:**
```bash
npm install                          # Root dependencies
npm run install:all                  # Frontend dependencies
cd backend && python3 -m venv venv && ./venv/bin/pip install -r requirements.txt
```

**Admin OAuth Setup:** Visit `http://localhost:5001/api/admin/spotify-setup?key=YOUR_ADMIN_SECRET`

## Architecture

```
Frontend (React 19/TypeScript/Vite)     Backend (Flask/Python)
├── pages/Landing.tsx                   ├── blueprints/
├── pages/MainApp.tsx                   │   ├── profile.py (user & playlist fetch)
├── context/UserContext.tsx             │   ├── generation.py (AI playlist gen)
├── context/GenerationContext.tsx       │   └── admin.py (OAuth setup)
├── components/features/                ├── services/
├── components/ui/                      │   ├── system_account.py (Spotify auth)
└── api/ (backend client)               │   ├── logic_api.py (AI integration)
                                        │   └── spotify.py (track operations)
                                        └── utils/rate_limit.py (session-based)
```

**Data Flow:**
1. User enters Spotify profile/playlist URL or text description
2. Backend fetches playlist data via Spotify API (Spotipy)
3. Logic.inc API analyzes playlist or generates from text
4. Backend searches for recommended tracks and adds to new playlist on system account
5. Frontend displays generated playlist

## Key Patterns

**Backend:**
- Flask App Factory Pattern in `app.py` with `create_app()`
- Blueprint-based routing organized by feature
- Service layer separation (business logic in `/services`, routes in `/blueprints`)
- Thread-safe Spotify token caching with expiry in `system_account.py`
- Session-based rate limiting (3 requests per 60 seconds)
- URL parsing helpers support multiple Spotify URL formats (http, URI, plain ID)

**Frontend:**
- React Context API for state management (UserContext, GenerationContext)
- React Router v7 for client-side routing
- Tailwind CSS utility-first styling

## Environment Variables

Required in `.env` (see `.env.example`):
- `SPOTIPY_CLIENT_ID`, `SPOTIPY_CLIENT_SECRET` - Spotify app credentials
- `LOGIC_API_TOKEN` - Logic.inc API key
- `ADMIN_SECRET` - Admin access key for OAuth setup
- `SPOTIFY_SYSTEM_REFRESH_TOKEN` - Obtained via OAuth setup flow
- `FLASK_ENV` - `development` or `production`

## API Endpoints

- `GET /api/profile/<username>` - Get user profile
- `GET /api/profile/<username>/playlists` - Get user's public playlists
- `POST /api/playlist/validate` - Validate playlist URL & get info
- `POST /api/generate/from-playlist` - Generate from existing playlist
- `POST /api/generate/from-text` - Generate from text description
