# Spotify Song Recommender

Song recommender using Logic's API

This is a demo project for [Logic.inc](https://logic.inc)

By connecting your Spotify account and importing your playlists, the song recommender is able to analyze your music taste and create a new playlist of new songs you might like that aren't already on your playlist.

## Screenshots
### Make a Playlist by Analyzing Your Music Taste
![playlist from playlist](/screenshots/playlist_from_playlist.png)
Have the Logic API analyze one of your existing playlists to learn your music taste, and create a new one from what it learns!

### Describe Your Ideal Playlist
![playlist from text](/screenshots/playlist_from_text.png)
Want to create an entirely new playlist? Describe your ideal playlist in text, and the Logic API will generate a new one for you

### Example Playlist
![example playlist](/screenshots/example_playlist.png)
Here's an example playlist made from one of my existing playlists. The Logic API noticed the themes of my existing playlist, that being early 2000s electronic music. Based on that knowledge, the Logic API chose new songs that fit that category!

The downloaded icons on some of the songs indicate that they were already elsewhere in my music library, so the Logic API has certainly correctly identified my taste in music!

## Hosting Yourself
Only a few short steps!

### Step 1: Download the repo
Clone the repo to your local machine!

### Step 2: Install the requirements in requirements.txt
Install the requirements by `cd`-ing into the project directory, and running `pip install -r requirements.txt`. Strongly recommend setting up a virtual environment. 

### Step 3: Create a Spotify developer app
Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard) and create a new app. Set the redirect URI to `http://127.0.0.1:5000` if you're running locally, and set a name of your choice! Make note of the Client ID and Client Secret, you'll need both of them later

If you want to host this project elsewhere, set the redirect URI to your domain.

### Step 4: Create the Logic documents
To generate the playlist, we're using Logic's API. Logic allows you to type up a document using natural language (like writing a Google Doc!) to describe what you want an LLM to do, and Logic will generate an API for you to use. 

Using this, we have an easy API to call to analyze music taste and suggest new songs!

You can see the example Logic documents under `/logic_documents` in this repo. Feel free to tweak as you see fit!

(For now, you'll need to set the addresses of your Logic docs inside the logic_api.py file)

### Step 4: Create a Logic API key
In the [Logic dashboard](https://app.logic.inc), select your account in the bottom left and choose `API Keys`. Create a new key, and make a note of it, you'll need it shortly.

### Step 5: Set environment variables and run!
You need to set 4 environment variables:
- `LOGIC_API_TOKEN` needs to be set to your Logic API key
- `SPOTIPY_REDIRECT_URI` needs to be set to 'http://127.0.0.1:5000' if you're hosting locally, otherwise choose the URI you chose in the Spotify developer app
- `SPOTIPY_CLIENT_ID` should be the client ID from the Spotify developer app you just made
- `SPOTIPY_CLIENT_SECRET` will be the secret from the Spotify developer app (it's hidden under a "View client secret" button right under the client ID)

Run the project with `python app.py`!