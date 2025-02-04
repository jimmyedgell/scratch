"""
Spotify Playlist CSV Converter

This script combines multiple Spotify playlist JSON files into a single CSV file,
formatting track durations and adding playlist information.

Created: 2024-03-19
Author: James
Version: 1.0
License: MIT
"""

import json
import pandas as pd
from pathlib import Path
from typing import List, Dict
from datetime import datetime

def format_duration(milliseconds: float) -> str:
    """
    Convert milliseconds to a formatted duration string (e.g., '4:32')
    
    Args:
        milliseconds: Duration in milliseconds
        
    Returns:
        Formatted duration string in 'M:SS' format
    """
    total_seconds = int(milliseconds / 1000)
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f"{minutes}:{seconds:02d}"

def combine_playlists_to_csv(input_dir: str = 'data/bronze', output_dir: str = 'data/silver') -> None:
    """
    Combine all playlist JSON files in the input directory into a single CSV file.
    
    Args:
        input_dir: Directory containing the playlist JSON files
        output_dir: Directory where the combined CSV will be saved
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # List to store all tracks
    all_tracks: List[Dict] = []
    
    # Process each JSON file in the input directory
    for json_file in input_path.glob('*.json'):
        print(f"Processing {json_file.name}...")
        
        with open(json_file, 'r', encoding='utf-8') as f:
            playlist_data = json.load(f)
        
        # Add playlist information to each track
        for track in playlist_data['tracks']:
            track_with_playlist = track.copy()
            track_with_playlist['playlist_name'] = playlist_data['playlist_name']
            track_with_playlist['playlist_url'] = playlist_data['playlist_url']
            all_tracks.append(track_with_playlist)
    
    if not all_tracks:
        print("No playlist files found!")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(all_tracks)
    
    # Format duration as M:SS
    df['duration'] = df['duration_ms'].apply(format_duration)
    
    # Convert added_at to datetime
    df['added_at'] = pd.to_datetime(df['added_at'])
    
    # Select and order columns
    columns = [
        'playlist_name', 'name', 'artist', 'album', 'duration', 
        'added_at', 'spotify_url', 'playlist_url'
    ]
    df = df[columns]
    
    # Save to CSV
    output_file = output_path / 'combined_playlists.csv'
    df.to_csv(output_file, index=False)
    
    # Print summary
    total_tracks = len(df)
    unique_artists = df['artist'].nunique()
    unique_albums = df['album'].nunique()
    unique_playlists = df['playlist_name'].nunique()
    
    print(f"\nProcessing complete!")
    print(f"Output saved to: {output_file}")
    print(f"\nSummary:")
    print(f"- Total playlists: {unique_playlists}")
    print(f"- Total tracks: {total_tracks}")
    print(f"- Unique artists: {unique_artists}")
    print(f"- Unique albums: {unique_albums}") 