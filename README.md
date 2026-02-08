# Spotify Song Recommender

![screenshot of user page](/screenshots/song_rec_user_page.png)

Get personalized playlist recommendations powered by the Logic API. This app uses [Logic.inc](https://logic.inc) to analyze your music taste and generate new playlists.

Use it here: [song-rec.romangarms.com](https://song-rec.romangarms.com/)

## Features

- **Analyze Your Playlists**: Have the AI analyze one of your existing playlists to learn your music taste and create a new playlist from what it learns
- **Describe Your Ideal Playlist**: Describe your ideal playlist in text, and the AI will generate one for you
- **No Login Required**: Just paste a public Spotify playlist - no OAuth login needed

## Quick Start

### 1. Install Dependencies

```bash
# Install root dependencies (for running both services)
npm install

# Install frontend dependencies
npm run install:all

# Install backend dependencies (create venv and install)
cd backend && python3 -m venv venv && ./venv/bin/pip install -r requirements.txt && cd ..
```

### 2. Set Up Environment Variables

Create a `.env` file in the project root:

```env
SPOTIPY_CLIENT_ID=your_spotify_client_id
SPOTIPY_CLIENT_SECRET=your_spotify_client_secret
SPOTIPY_REDIRECT_URI=http://127.0.0.1:5001/api/admin/callback
LOGIC_API_TOKEN=your_logic_api_token
ADMIN_SECRET=your_admin_secret
SPOTIFY_SYSTEM_REFRESH_TOKEN=your_refresh_token
```

### 3. Run the App

```bash
npm run dev
```

This builds the frontend and starts the server on port 5001. The frontend auto-rebuilds when you change files.

**Open http://localhost:5001** in your browser.

## Initial Setup

### Getting Your Spotify Credentials

1. Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Create a new app
3. Set the redirect URI to `http://127.0.0.1:5001/api/admin/callback`
4. Copy the Client ID and Client Secret

### Getting Your Logic API Key

1. Go to the [Logic dashboard](https://app.logic.inc)
2. Select your account → API Keys
3. Create a new key

### Setting Up the System Account

The app uses a "system account" to create playlists on behalf of users. To set this up:

1. Start the app: `npm run dev`
2. Visit `http://localhost:5001/api/admin/spotify-setup?key=YOUR_ADMIN_SECRET`
3. Authorize with the Spotify account you want to use as the system account
4. Copy the refresh token and add it to your `.env` as `SPOTIFY_SYSTEM_REFRESH_TOKEN`

## Project Structure

```
├── package.json           # Root scripts (npm run dev)
├── .env                   # Environment variables
├── backend/               # Flask API
│   ├── app.py
│   ├── blueprints/        # API routes
│   ├── services/          # Business logic
│   └── utils/             # Utilities
└── frontend/              # React app
    ├── src/
    │   ├── components/    # UI components
    │   ├── context/       # State management
    │   ├── pages/         # Page components
    │   └── api/           # API client
    └── ...
```

## Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Build frontend + start server with auto-rebuild |
| `npm run dev:backend` | Start only the backend |
| `npm run build` | Build the frontend for production |
| `npm run start` | Start the server (production) |

## Tech Stack

- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS
- **Backend**: Flask, Spotipy
- **AI**: Logic.inc API
