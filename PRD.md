# PRD: Spotify Song Recommender - React Migration

## Overview

Convert the existing Flask + Jinja2 application to a modern React frontend with a reorganized Flask API backend. This migration modernizes the tech stack, improves maintainability, and enables a better user experience with a refreshed UI design.

## Goals

1. **Modernize Frontend**: Replace Jinja2 templates with a React SPA using TypeScript
2. **Improve Backend Organization**: Restructure Flask routes using Blueprints, organized by feature
3. **Refresh UI Design**: Implement a card-based 3-column layout for the main app while preserving the landing page aesthetic
4. **Maintain Functionality**: All existing features must work identically after migration

## Tech Stack

### Frontend
| Technology | Purpose |
|------------|---------|
| React 18 | UI framework |
| TypeScript | Type safety |
| Vite | Build tool & dev server |
| Tailwind CSS | Styling |
| React Router | Client-side routing |
| React Context + Hooks | State management |

### Backend
| Technology | Purpose |
|------------|---------|
| Flask | API framework |
| Flask Blueprints | Route organization |
| Spotipy | Spotify API integration |
| Existing logic modules | LLM/Logic.inc API calls |

## Architecture

### Frontend Structure

```
/frontend
├── src/
│   ├── main.tsx                 # App entry point
│   ├── App.tsx                  # Root component with router
│   ├── index.css                # Tailwind imports + global styles
│   ├── components/
│   │   ├── ui/                  # Reusable UI components (Button, Card, Input, etc.)
│   │   ├── layout/              # Layout components (Header, Sidebar, Column)
│   │   └── features/            # Feature-specific components
│   │       ├── profile/         # ProfileCard, ProfileInput
│   │       ├── playlist/        # PlaylistList, PlaylistCard, PlaylistSelector
│   │       └── generation/      # GenerationTabs, ResultCard, TextInput
│   ├── pages/
│   │   ├── Landing.tsx          # Landing page (profile URL input)
│   │   └── App.tsx              # Main 3-column app layout
│   ├── context/
│   │   ├── UserContext.tsx      # User profile state
│   │   └── GenerationContext.tsx # Playlist generation state
│   ├── hooks/
│   │   ├── useProfile.ts        # Profile fetching logic
│   │   ├── usePlaylists.ts      # Playlist fetching logic
│   │   └── useGeneration.ts     # Generation API calls
│   ├── api/
│   │   └── client.ts            # API client (fetch wrapper)
│   └── types/
│       └── index.ts             # TypeScript interfaces
├── index.html
├── vite.config.ts
├── tailwind.config.js
├── tsconfig.json
└── package.json
```

### Backend Structure

```
/backend
├── app.py                       # Flask app factory, CORS setup
├── config.py                    # Configuration management
├── blueprints/
│   ├── __init__.py
│   ├── profile.py               # /api/profile/* routes
│   │   └── GET /api/profile/<username> - Fetch user profile
│   │   └── GET /api/profile/<username>/playlists - Fetch user playlists
│   ├── generation.py            # /api/generate/* routes
│   │   └── POST /api/generate/from-playlist - Generate from playlist analysis
│   │   └── POST /api/generate/from-text - Generate from text description
│   └── admin.py                 # /api/admin/* routes (token setup)
├── services/
│   ├── __init__.py
│   ├── spotify.py               # Spotify API operations (from logic/spotify.py)
│   ├── system_account.py        # System account management (from logic/system_account.py)
│   └── logic_api.py             # Logic.inc API calls (from logic/logic_api.py)
├── utils/
│   ├── __init__.py
│   └── rate_limit.py            # Rate limiting logic
└── requirements.txt
```

### API Endpoints

| Method | Endpoint | Description | Request | Response |
|--------|----------|-------------|---------|----------|
| GET | `/api/profile/{username}` | Fetch user profile | - | `{ id, display_name, images, external_urls }` |
| GET | `/api/profile/{username}/playlists` | Get user's public playlists | - | `{ playlists: [...] }` |
| GET | `/api/playlist/{playlist_id}/tracks` | Get playlist tracks | - | `{ tracks: [...] }` |
| POST | `/api/generate/from-playlist` | Generate from playlist | `{ playlist_id: string }` | `{ playlist_url, title, description }` |
| POST | `/api/generate/from-text` | Generate from description | `{ description: string }` | `{ playlist_url, title, description }` |

## UI Design

### Landing Page
- **Keep existing design aesthetic**: Dark Spotify theme (#000000 bg, #1DB954 accent)
- Migrate styles to Tailwind classes
- Profile URL/username input with validation
- Recent searches from localStorage

### Main App - 3 Column Layout

```
┌─────────────────────────────────────────────────────────────────┐
│                          Header                                  │
├──────────────┬────────────────────────┬────────────────────────┤
│              │                        │                         │
│   Profile    │    Input Selection     │    Generated Output    │
│    Card      │                        │                         │
│              │  ┌──────────────────┐  │    ┌───────────────┐   │
│  ┌────────┐  │  │ [Playlist] [Text]│  │    │  Result Card  │   │
│  │ Avatar │  │  └──────────────────┘  │    │               │   │
│  └────────┘  │                        │    │  Playlist     │   │
│              │  ┌──────────────────┐  │    │  Title        │   │
│  Username    │  │                  │  │    │               │   │
│              │  │  Playlist List   │  │    │  Description  │   │
│  Stats       │  │  (scrollable)    │  │    │               │   │
│              │  │                  │  │    │  [Open in     │   │
│              │  │  - Playlist 1    │  │    │   Spotify]    │   │
│              │  │  - Playlist 2    │  │    │               │   │
│              │  │  - Playlist 3    │  │    └───────────────┘   │
│              │  │                  │  │                         │
│              │  └──────────────────┘  │                         │
│              │                        │                         │
│              │  [Generate Button]     │                         │
│              │                        │                         │
└──────────────┴────────────────────────┴────────────────────────┘
```

### Column Details

**Left Column - Profile Card**
- User avatar image
- Display name
- Spotify profile link
- Option to change user

**Middle Column - Input Selection**
- Tab navigation: "From Playlist" | "From Text" | (future tabs)
- **Playlist Tab**:
  - Scrollable list of user's playlists with cover art
  - Or paste external playlist URL
  - Selected playlist highlighted
- **Text Tab**:
  - Textarea for describing desired playlist
  - Example prompts/suggestions
- Generate button at bottom

**Right Column - Generated Output**
- Empty state with instructions before generation
- Loading state during generation
- Result card showing:
  - Generated playlist cover/title
  - AI-generated description
  - Track preview list (collapsible)
  - "Open in Spotify" button
  - "Generate Another" option

### Responsive Behavior
- Desktop (>1024px): Full 3-column layout
- Tablet (768-1024px): 2 columns (profile collapses to header)
- Mobile (<768px): Single column, stacked layout

## Implementation Phases

### Phase 1: Project Setup
- Initialize Vite + React + TypeScript project in `/frontend`
- Configure Tailwind CSS
- Set up React Router with placeholder pages
- Reorganize Flask backend into blueprint structure
- Configure CORS for local development
- Verify API endpoints work with existing functionality

### Phase 2: API Layer
- Create Flask blueprints for profile, generation, admin
- Move route logic from app.py to appropriate blueprints
- Refactor services layer (spotify, system_account, logic_api)
- Add proper error handling and JSON responses
- Test all endpoints independently

### Phase 3: Core React Components
- Build reusable UI components (Button, Card, Input, Tabs)
- Create layout components (Header, ThreeColumnLayout)
- Implement React Context for user and generation state
- Build API client with error handling

### Phase 4: Landing Page
- Port landing page design to React + Tailwind
- Implement profile URL input with validation
- Add localStorage for recent searches
- Connect to profile API

### Phase 5: Main App - Profile & Playlists
- Build ProfileCard component
- Implement playlist fetching and display
- Create PlaylistCard with selection state
- Add external playlist URL input option

### Phase 6: Main App - Generation
- Build tab navigation component
- Implement "From Playlist" generation flow
- Implement "From Text" generation flow
- Create result display with loading states
- Handle errors gracefully

### Phase 7: Polish & Testing
- Responsive design implementation
- Loading states and animations
- Error boundary components
- Cross-browser testing
- Performance optimization

## Migration Strategy

1. **Parallel Development**: Build React frontend alongside existing Jinja templates
2. **API First**: Ensure all Flask endpoints return JSON before building React components
3. **Feature Parity**: Match all existing functionality before adding enhancements
4. **Gradual Cutover**: Can run both versions during development via different ports

## Success Criteria

- [ ] All existing features work in React version
- [ ] Landing page matches current design aesthetic
- [ ] Main app uses new 3-column card-based layout
- [ ] Backend organized into feature-based blueprints
- [ ] TypeScript compilation passes with no errors
- [ ] Responsive design works on mobile, tablet, desktop
- [ ] Rate limiting still functional
- [ ] Admin token setup still works

## Out of Scope

- New features beyond UI refresh
- Authentication changes (still using system account model)
- Database/persistence changes
- Deployment configuration changes
- Unit/integration test suite (can be added later)

## Open Questions

1. Should we add any loading skeleton animations?
2. Preference for Tailwind component library (Headless UI, Radix, etc.) or custom components?
3. Should generated playlist show full track list or just preview?
