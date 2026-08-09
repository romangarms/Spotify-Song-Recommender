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

Since Spotify's February 2026 changes, only search and playlist metadata work
without a user token. Two auth flows are used, both in `system_account.py`:

**Client Credentials (`get_public_spotify`) — no expiry:**
| Endpoint | Purpose | Limitation |
|----------|---------|------------|
| `GET /v1/search` | Search tracks/playlists | Max 10 results; null entries for inaccessible playlists |
| `GET /v1/playlists/{id}` | Playlist metadata | Name, owner, images only — returns **no** track list or count |

**System Account User Token (`get_system_spotify`) — expires every 6 months:**
| Endpoint | Purpose |
|----------|---------|
| `GET /v1/me` | System account profile |
| `POST /v1/me/playlists` | Create playlist (the `/users/{id}/playlists` path now 403s) |
| `PUT /v1/playlists/{playlist_id}` | Update playlist name/description |
| `POST /v1/playlists/{playlist_id}/items` | Add tracks (max 100 per request) |
| `GET /v1/playlists/{id}/items` | Tracks — **only for playlists the system account owns** |

### Blocked in Development Mode (403, no token can fix)

Verified against the live API — these fail regardless of auth flow or scopes:
- `GET /v1/users/{id}` — any user profile
- `GET /v1/users/{id}/playlists` — any user's playlist list
- `GET /v1/playlists/{id}/items` — items of any playlist the system account
  does not own, however public it is

Extended Quota Mode, the only exemption, is closed to new apps (Spotify
stopped onboarding apps that were not already approved in November 2024, and
now requires a registered business with ~250K MAU). Allowlisting the playlist
owner does **not** help — access is keyed to ownership, not the allowlist.

**Consequence:** reading someone else's playlist is impossible, so the app
takes seed songs directly instead — via track search and pasted song links.
The profile-browsing and generate-from-playlist flows were removed rather
than left broken; see git history for that code.

### Refresh Token Expiry (6 months)

Spotify expires refresh tokens 6 months after authorization, and refreshing
does **not** extend that window. When the token dies, `refresh_access_token`
raises `SystemTokenExpiredError`; the app-level handler in `app.py` returns a
single 503 `system_token_expired` response. The token is discarded rather than
retried, per Spotify's guidance.

Recovery is manual and requires a browser login: visit
`/api/admin/spotify-setup?key=ADMIN_SECRET`, then update
`SPOTIFY_SYSTEM_REFRESH_TOKEN` and restart. The authorization date is recorded
in `backend/token_metadata.json`; `GET /api/admin/debug-env` reports days
remaining, and token refreshes log a warning from day 150.

Search and the playlist owner lookup keep working while the token is dead;
everything else degrades to 503.

**App owner must have Spotify Premium** — development mode apps return 403 on
every call otherwise.

### Data Limitations

**Can Access:** Spotify's public search index, public playlist metadata, and the system account's own playlists and their tracks

**Cannot Access:** Any user profile, any user's playlist list, the tracks of any playlist the system account does not own, private playlists, "Liked Songs" or library, listening history, private user info

### OAuth Scopes (Admin Setup Only)
Defined once as `SYSTEM_ACCOUNT_SCOPES` in `services/system_account.py`:
- `playlist-modify-public` / `playlist-modify-private` - Create/edit playlists on system account
- `playlist-read-private` / `playlist-read-collaborative` - Read playlist items
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
├── pages/MainApp.tsx                   │   ├── generation.py (search + AI gen)
├── context/GenerationContext.tsx       │   └── admin.py (OAuth setup)
├── components/features/                ├── services/
├── components/ui/                      │   ├── system_account.py (Spotify auth)
└── api/ (backend client)               │   ├── logic_api.py (AI integration)
                                        │   └── spotify.py (track operations)
                                        └── utils/rate_limit.py (session-based)
```

**Data Flow:**
1. User picks seed songs (search) or pastes Spotify song links, or writes a description
2. Backend resolves each track via `GET /tracks/{id}` on client credentials
3. Logic.inc API infers taste from the seeds, or generates from text
4. Backend searches for recommended tracks and adds to a new playlist on the system account
5. Frontend displays generated playlist

Generation always creates a draft playlist first; `build_playlist` in
`blueprints/generation.py` discards it if population fails, so failures do not
strand "GEN: Work in Progress" playlists on the system account.

## Key Patterns

**Backend:**
- Flask App Factory Pattern in `app.py` with `create_app()`
- Blueprint-based routing organized by feature
- Service layer separation (business logic in `/services`, routes in `/blueprints`)
- Thread-safe Spotify token caching with expiry in `system_account.py`
- Session-based rate limiting (3 requests per 60 seconds)
- `parse_track_ids_from_text` accepts links, URIs, and bare IDs in any mix

**Frontend:**
- React Context API for state management (GenerationContext)
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

- `GET /api/search/tracks` - Search tracks to use as seeds (max 10 results)
- `POST /api/tracks/resolve` - Turn pasted Spotify song links into track details
- `POST /api/generate/from-tracks` - Generate from seed track IDs
- `POST /api/generate/from-text` - Generate from text description
