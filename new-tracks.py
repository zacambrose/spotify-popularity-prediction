import json
import pandas as pd
file_path = '/Users/zacambrose/Desktop/Spotify Popularity Prediction DSCI 303/new_tracks_data.json'

with open(file_path, 'r') as file:
    new_tracks_data = json.load(file)


flattened_data = []

for album_id, album_data in new_tracks_data.items():
    for track_info, audio_feature in zip(album_data['tracks'], album_data['audio_features']):
        combined_data = {**track_info, **audio_feature}
        combined_data['album_id'] = album_id
        flattened_data.append(combined_data)

tracks_df = pd.DataFrame(flattened_data)

csv_file_path = '/Users/zacambrose/Desktop/Spotify Popularity Prediction DSCI 303/new_tracks_data_final2.csv'
tracks_df.to_csv(csv_file_path, index=False)