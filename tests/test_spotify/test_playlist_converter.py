"""
Unit tests for spotify_playlist_csv_converter.py
"""

import pytest
from pathlib import Path
import json
import pandas as pd
from src.spotify import format_duration, combine_playlists_to_csv

def test_format_duration():
    """Test the duration formatting function"""
    # Test various durations
    assert format_duration(1000) == "0:01"  # 1 second
    assert format_duration(60000) == "1:00"  # 1 minute
    assert format_duration(61000) == "1:01"  # 1 minute 1 second
    assert format_duration(3661000) == "61:01"  # 61 minutes 1 second
    assert format_duration(0) == "0:00"  # 0 seconds

@pytest.fixture
def sample_playlist_data(tmp_path):
    """Create sample playlist JSON files for testing"""
    bronze_dir = tmp_path / "bronze"
    bronze_dir.mkdir()
    
    # Create two sample playlist files
    playlist1 = {
        "playlist_name": "Test Playlist 1",
        "playlist_id": "123",
        "playlist_url": "http://example.com/1",
        "tracks": [
            {
                "name": "Song 1",
                "artist": "Artist 1",
                "album": "Album 1",
                "duration_ms": 180000,
                "spotify_url": "http://example.com/song1",
                "added_at": "2024-03-19T12:00:00Z"
            }
        ]
    }
    
    playlist2 = {
        "playlist_name": "Test Playlist 2",
        "playlist_id": "456",
        "playlist_url": "http://example.com/2",
        "tracks": [
            {
                "name": "Song 2",
                "artist": "Artist 2",
                "album": "Album 2",
                "duration_ms": 240000,
                "spotify_url": "http://example.com/song2",
                "added_at": "2024-03-19T12:00:00Z"
            }
        ]
    }
    
    # Write the sample files
    with open(bronze_dir / "playlist1.json", 'w') as f:
        json.dump(playlist1, f)
    with open(bronze_dir / "playlist2.json", 'w') as f:
        json.dump(playlist2, f)
    
    return tmp_path

def test_combine_playlists_to_csv(sample_playlist_data):
    """Test the playlist combination function"""
    # Set up paths
    input_dir = sample_playlist_data / "bronze"
    output_dir = sample_playlist_data / "silver"
    
    # Run the combination function
    combine_playlists_to_csv(str(input_dir), str(output_dir))
    
    # Check if output file exists
    output_file = output_dir / "combined_playlists.csv"
    assert output_file.exists()
    
    # Read and verify the output
    df = pd.read_csv(output_file)
    
    # Check basic properties
    assert len(df) == 2  # Two tracks total
    assert list(df.columns) == [
        'playlist_name', 'name', 'artist', 'album', 'duration',
        'added_at', 'spotify_url', 'playlist_url'
    ]
    
    # Check content
    assert "Test Playlist 1" in df['playlist_name'].values
    assert "Test Playlist 2" in df['playlist_name'].values
    assert "3:00" in df['duration'].values  # 180000ms = 3:00
    assert "4:00" in df['duration'].values  # 240000ms = 4:00 