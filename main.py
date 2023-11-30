import requests
import urllib.parse
from datetime import datetime, timedelta
from flask import Flask, redirect, request, jsonify, session, send_file
import pandas as pd
import json
app = Flask(__name__)
app.secret_key = 'amubean'

CLIENT_ID = '04215e23f121469399713212f3a45411'
CLIENT_SECRET = '44feec73607242bfa1b23db1708d0c2e'
REDIRECT_URI = 'http://localhost:5000/callback'

AUTH_URL = 'https://accounts.spotify.com/authorize'
TOKEN_URL = 'https://accounts.spotify.com/api/token'
API_BASE_URL = 'https://api.spotify.com/v1/'

@app.route('/')
def index():
    return "Welcome to my Spotify App <a href='/login'>Login with Spotify</a>"

@app.route('/login')
def login():
    scope = 'user-read-private user-read-email'

    params = {
        'client_id': CLIENT_ID,
        'response_type': 'code',
        'scope': scope,
        'redirect_uri': REDIRECT_URI,
        'show_dialog': True
    }
    auth_url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"

    return redirect(auth_url)

@app.route('/callback')
def callback():
    if 'error' in request.args:
        return jsonify({"error": request.args['error']})
    
    if 'code' in request.args:
        req_body = {
            'code': request.args['code'],
            'grant_type': 'authorization_code',
            'redirect_uri': REDIRECT_URI,
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET
        }

        response = requests.post(TOKEN_URL,data=req_body)
        token_info = response.json()

        session['access_token'] = token_info['access_token'] # lasts for 1 day
        session['refresh_token'] = token_info['refresh_token'] # lets us access access token again
        session['expires_at'] = datetime.now().timestamp() + token_info['expires_in']

        return redirect('/album-tracks')

@app.route('/new-releases')
def get_new_releases():
    if 'access_token' not in session:
        return redirect('/login')
    
    if datetime.now().timestamp() > session['expires_at']:
        return redirect('/refresh-token')
    
    headers = {
        'Authorization': f"Bearer {session['access_token']}"
    }
    response = requests.get(API_BASE_URL + 'browse/new-releases', headers=headers)
    newreleases = response.json()
    current_date = datetime.now().strftime("%Y-%m-%d")
    filename = f'new_releases_{current_date}.json'
    with open(filename, 'w') as file:
        file.write(json.dumps(newreleases))

    return jsonify(newreleases)

@app.route('/download-new-releases')
def download_new_releases():
    return send_file('new_releases.json', as_attachment=True)

@app.route('/album-tracks')
def get_album_tracks():
    new_releases_df = pd.read_csv('/Users/zacambrose/Downloads/New Spotify Releases/new-releases.csv')
    albums_df = new_releases_df[new_releases_df['album_type'] == 'album']
    album_tracks_data = {}

    for _, album in albums_df.iterrows():
        album_id = album['id']
        album_tracks_data[album_id] = {
            'tracks': [],
            'audio_features': []
        }
        
        # Get tracks for the album
        tracks_response = requests.get(API_BASE_URL + f'albums/{album_id}/tracks',
                                       headers={'Authorization': f"Bearer {session.get('access_token')}"})
        tracks_data = tracks_response.json()

        # Check if tracks data is available and extract track IDs
        if tracks_data and 'items' in tracks_data:
            for track in tracks_data['items']:
                track_info = {
                    'id': track['id'],
                    'name': track['name'],
                    'uri': track['uri'],
                    'external_urls': track['external_urls'],
                    'artists': ', '.join(artist['name'] for artist in track['artists'])  # Join artist names
                }
                album_tracks_data[album_id]['tracks'].append(track_info)
        else:
            print(f"No track data available for album {album_id}")
            continue

        track_ids = [track['id'] for track in album_tracks_data[album_id]['tracks']]

        # Get audio features for the tracks
        audio_features_response = requests.get(API_BASE_URL + f'audio-features?ids={",".join(track_ids)}',
                                               headers={'Authorization': f"Bearer {session.get('access_token')}"})
        audio_features_data = audio_features_response.json()

        # Check if audio features data is available
        if audio_features_data and 'audio_features' in audio_features_data:
            for feature, track in zip(audio_features_data['audio_features'], album_tracks_data[album_id]['tracks']):
                # Check if feature data is not None
                if feature:
                    audio_feature_info = {key: feature[key] for key in ['danceability', 'energy', 'loudness', 'speechiness',
                                                                        'acousticness', 'instrumentalness', 'liveness',
                                                                        'valence', 'tempo'] if key in feature}
                    # Combine track info and audio features
                    combined_data = {**track, **audio_feature_info}
                    album_tracks_data[album_id]['audio_features'].append(combined_data)
        else:
            # Handle the case where no audio features are returned
            print(f"No audio features data available for tracks in album {album_id}")
            
    filename = 'new_tracks_data.json'
    with open(filename, 'w') as file:
        file.write(json.dumps(album_tracks_data))

    return jsonify(album_tracks_data)

@app.route('/download-album-tracks')
def download_album_tracks():
    return send_file('new_tracks_data.json', as_attachment=True)

@app.route('/refresh-token')
def refresh_token():
    if 'refresh_token' not in session:
        return redirect('/login')
    if datetime.now().timestamp() > session['expires_at']:
        req_body = {
            'grant_type': 'refresh_token',
            'refresh_token': session['refresh_token'],
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET
        }
        response = requests.post(TOKEN_URL,data=req_body)
        new_token_info = response.json()
        
        session['access_token'] = new_token_info['access_token']
        session['expires_at'] = datetime.now().timestamp() + new_token_info['expires_in']

        return redirect('/new-releases')

if __name__ == '__main__':
    app.run(host='0.0.0.0',debug=True)