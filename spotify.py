import yaml
import spotipy
from spotipy import SpotifyOAuth

stream = open('Spotify/spotify.yaml')
spotify_details = yaml.safe_load(stream)
CLIENT_ID = spotify_details['CLIENT_ID']
CLIENT_SECRET = spotify_details['CLIENT_SECRET']
REDIRECT_URL = 'https://localhost:8888/callback'

#initialize the spotify client
client_manager = SpotifyOAuth(client_id=CLIENT_ID, 
                                          client_secret=CLIENT_SECRET, 
                                          redirect_uri=REDIRECT_URL,
                                          scope='playlist-read-private')
sp = spotipy.Spotify(auth_manager=client_manager)