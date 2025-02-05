"""Tests for the playlist CSV converter module"""

# Standard imports
import json
from pathlib import Path
from unittest.mock import patch

# Third party imports
import pandas as pd
import pytest

# Local imports
from src.spotify.playlist_csv_converter import (
    format_duration,
    combine_playlists_to_csv
)


@pytest.fixture
def mock_playlist_data():
    """Mock playlist JSON data"""
    return {
        'playlist_name': 'Test Playlist',
        'tracks': [
            {
                'name': 'Test Track 1',
                'artist': 'Test Artist 1',
                'album': 'Test Album 1',
                'duration_ms': 180000,
                'spotify_url': 'https://spotify.com/track/1',
                'added_at': '2024-03-19T12:00:00Z'
            },
            {
                'name': 'Test Track 2',
                'artist': 'Test Artist 2',
                'album': 'Test Album 2',
                'duration_ms': 240000,
                'spotify_url': 'https://spotify.com/track/2',
                'added_at': '2024-03-19T12:01:00Z'
            }
        ]
    }


def test_format_duration():
    """Test duration formatting from milliseconds to MM:SS"""
    test_cases = [
        (180000, '3:00'),    # 3 minutes
        (195000, '3:15'),    # 3 minutes 15 seconds
        (45000, '0:45'),     # 45 seconds
        (3600000, '60:00'),  # 1 hour
        (0, '0:00'),         # 0
    ]
    
    for ms, expected in test_cases:
        assert format_duration(ms) == expected

def test_combine_playlists_to_csv(tmp_path, mock_playlist_data):
    """Test combining playlist JSON files into CSV"""
    # Create mock bronze and silver directories
    bronze_dir = tmp_path / 'data' / 'bronze'
    bronze_dir.mkdir(parents=True)
    
    # Create a test playlist file
    playlist_file = bronze_dir / 'test_playlist.json'
    with open(playlist_file, 'w', encoding='utf-8') as f:
        json.dump(mock_playlist_data, f)
    
    # Mock the Path to use our temporary directory
    def mock_path_constructor(path_str):
        if path_str == 'data/bronze':
            return bronze_dir
        if path_str == 'data/silver':
            return tmp_path / 'data' / 'silver'
        return Path(path_str)
    
    with patch('src.spotify.playlist_csv_converter.Path', side_effect=mock_path_constructor):
        output_file = combine_playlists_to_csv()
        
        # Verify the output file exists
        assert output_file.exists()
        
        # Read and verify the CSV content
        df = pd.read_csv(output_file)
        assert len(df) == 2  # Two tracks
        assert 'playlist' in df.columns
        assert all(df['playlist'] == 'Test Playlist')
        assert all(df['duration'].str.match(r'^\d+:\d{2}$'))  # Format MM:SS

def test_combine_playlists_no_bronze_dir(tmp_path):
    """Test error handling when bronze directory doesn't exist"""
    # Create a mock Path class that makes bronze_dir.exists() return False
    class MockPath:
        def __init__(self, path):
            self.path = path
        
        def exists(self):
            return False
        
        def mkdir(self, parents=False, exist_ok=False):
            pass
        
        def glob(self, pattern):
            return []
    
    with patch('src.spotify.playlist_csv_converter.Path', side_effect=MockPath):
        with pytest.raises(FileNotFoundError, match="No bronze directory found"):
            combine_playlists_to_csv()

def test_combine_playlists_empty_bronze_dir(tmp_path):
    """Test error handling when bronze directory is empty"""
    # Create empty bronze directory
    bronze_dir = tmp_path / 'data' / 'bronze'
    bronze_dir.mkdir(parents=True)
    
    def mock_path_constructor(path_str):
        if path_str == 'data/bronze':
            return bronze_dir
        if path_str == 'data/silver':
            return tmp_path / 'data' / 'silver'
        return Path(path_str)
    
    with patch('src.spotify.playlist_csv_converter.Path', side_effect=mock_path_constructor):
        with pytest.raises(FileNotFoundError, match="No playlist files found"):
            combine_playlists_to_csv()

def test_combine_playlists_invalid_json(tmp_path):
    """Test handling of invalid JSON files"""
    # Create bronze directory with invalid JSON
    bronze_dir = tmp_path / 'data' / 'bronze'
    bronze_dir.mkdir(parents=True)
    
    invalid_file = bronze_dir / 'invalid.json'
    invalid_file.write_text('{invalid json}')
    
    def mock_path_constructor(path_str):
        if path_str == 'data/bronze':
            return bronze_dir
        if path_str == 'data/silver':
            return tmp_path / 'data' / 'silver'
        return Path(path_str)
    
    with patch('src.spotify.playlist_csv_converter.Path', side_effect=mock_path_constructor):
        with pytest.raises(ValueError, match="No tracks were found"):
            combine_playlists_to_csv() 