from flask import Flask, render_template, request, url_for, flash, redirect, Response, jsonify
from collections import defaultdict
import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.oauth2 import SpotifyOAuth


"""
SPOTIPY
"""

os.environ['SPOTIPY_CLIENT_ID']='5e4dee102e1742f78a7a1d4c38f6cc89'
os.environ['SPOTIPY_CLIENT_SECRET']='d67d6648e4a54bfda09c6219cd0edc97'
os.environ['SPOTIPY_REDIRECT_URI']='http://localhost:8080'
scope = ["user-library-read", "user-top-read", "user-read-recently-played", ]
if os.path.exists('.cache'): os.remove('.cache')

spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))

# Top Tracks
top_tracks = sp.current_user_top_tracks()

# Top Artists
top_artists = sp.current_user_top_artists(limit=100, time_range='long_term')

# Top Genres
top_tracks_lt = sp.current_user_top_tracks(limit=100, time_range='long_term')
top_genres = defaultdict(float)
for song in top_tracks_lt['items']:
    for artist in song['artists']:
        genres = sp.artist(artist['id'])['genres']
        if genres: top_genres[genres[0]] += 1
sorted_genres = {k: v for k, v in sorted(top_genres.items(), key=lambda item: item[1], reverse=True)[:6]}
sum_other = sum(v for k, v in sorted(top_genres.items(), key=lambda item: item[1], reverse=True)[6:])
sorted_genres['other'] = sum_other

# Average BPM
ave_bpm = 0
song_bpm = defaultdict()
for song in top_tracks_lt['items']:
    data = sp.audio_features(song['id'])[0]
    ave_bpm += data['tempo']
    song_bpm[song['id']] = data['tempo']
ave_bpm /= len(top_tracks_lt['items'])
ave_bpm = int(ave_bpm)
diff = {x : abs(y - ave_bpm) for x, y in song_bpm.items()}
closest_id = min(diff, key=diff.get)
closest_song = sp.track(closest_id)
closest_bpm = song_bpm.get(min(diff, key=diff.get))
closest_bpm = int(closest_bpm)

# Danceability vs Energy
top_20_tracks = top_tracks_lt['items'][:20]
dance_energy = defaultdict()
for track in top_20_tracks:
    features = sp.audio_features(track['id'])[0]
    dance_energy[track['name']] = (features['danceability'], features['energy'])

# Popularity
popularity = defaultdict()
for track in top_tracks_lt['items']:
    popularity[track['id']] = track['popularity']
num_pop = sum([y/y for y in popularity.values() if y > 60])
pop = num_pop/len(top_tracks_lt['items'])
least_pop = sp.track(min(popularity, key=popularity.get)) 
least_val = min(popularity.items(), key=lambda x: x[1])[1]
most_pop = sp.track(max(popularity, key=popularity.get)) 
most_val = max(popularity.items(), key=lambda x: x[1])[1]


"""
FLASK
"""

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24).hex()

@app.route('/')
def index():
    return render_template('index.html', top_tracks=top_tracks, top_artists=top_artists)

@app.route('/about/')
def about():
    return render_template('about.html')

@app.route('/visualizations/')
def visualizations():
    return render_template('visualizations.html', sorted_genres=sorted_genres, ave_bpm=ave_bpm, closest_song=closest_song, closest_bpm=closest_bpm, pop=pop, least_pop=least_pop, least_val=least_val, most_pop=most_pop, most_val=most_val, dance_energy=dance_energy)
