import pandas as pd
import json
file_paths = ['/Users/zacambrose/Downloads/New Spotify Releases/new_releases_2023-11-12.json',
              '/Users/zacambrose/Downloads/New Spotify Releases/new_releases_2023-11-13.json',
              '/Users/zacambrose/Downloads/New Spotify Releases/new_releases_2023-11-21.json',
              '/Users/zacambrose/Downloads/New Spotify Releases/new_releases_2023-11-27.json']
              

all_songs_info = []
def extract_song_info(item):
    return {
        'album_type': item.get('album_type'),
        'artists': ', '.join(artist['name'] for artist in item.get('artists', [])),
        'external_urls': item.get('external_urls', {}).get('spotify'),
        'href': item.get('href'),
        'id': item.get('id'),
        'name': item.get('name'),
        'release_date': item.get('release_date'),
        'total_tracks': item.get('total_tracks'),
        'type': item.get('type'),
        'uri': item.get('uri'),
    }

for file_path in file_paths:
    with open(file_path, 'r') as file:
        json_data = json.load(file)
        items = json_data.get('albums', {}).get('items', [])
        for item in items:
            song_info = extract_song_info(item)
            all_songs_info.append(song_info)

songs_df = pd.DataFrame(all_songs_info)
songs_df = songs_df.drop_duplicates()
songs_df.to_csv('/Users/zacambrose/Downloads/New Spotify Releases/new-releases.csv')