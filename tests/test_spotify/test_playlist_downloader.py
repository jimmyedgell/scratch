"""Tests for the playlist downloader module"""

import pytest
from pathlib import Path
import json
from unittest.mock import Mock, patch

from src.spotify.playlist_downloader import (
    sanitize_filename,
    extract_track_info,
    save_tracks_to_json,
    process_track_batch
)

@pytest.fixture
def mock_track():
    """Mock track data"""
    return {
        'name': 'Test Track',
        'artists': [{'name': 'Test Artist'}],
        'album': {'name': 'Test Album'},
        'duration_ms': 180000,
        'external_urls': {'spotify': 'https://spotify.com/track/123'}
    }

@pytest.fixture
def mock_user_info():
    """Mock user information"""
    return {
        'id': 'test_user',
        'display_name': 'Test User'
    }

def test_sanitize_filename():
    """Test filename sanitization"""
    test_cases = [
        ('Hello World!', 'hello_world'),
        ('My Playlist #1', 'my_playlist_1'),
        ('Weird///Chars???', 'weird_chars'),
        ('   Spaces   ', 'spaces'),
        ('UPPER_case', 'upper_case')
    ]
    
    for input_name, expected in test_cases:
        assert sanitize_filename(input_name) == expected

def test_extract_track_info(mock_track):
    """Test track information extraction"""
    added_at = '2024-03-19T12:00:00Z'
    result = extract_track_info(mock_track, added_at)
    
    assert result == {
        'name': 'Test Track',
        'artist': 'Test Artist',
        'album': 'Test Album',
        'duration_ms': 180000,
        'spotify_url': 'https://spotify.com/track/123',
        'added_at': added_at
    }

def test_save_tracks_to_json(mock_user_info, tmp_path):
    """Test saving tracks to JSON file"""
    # Create the bronze directory in the temporary path
    bronze_dir = tmp_path / 'data' / 'bronze'
    bronze_dir.mkdir(parents=True)
    
    # Mock the Path calls to use our temporary directory
    def mock_path_constructor(path_str):
        if path_str == 'data/bronze':
            return bronze_dir
        return Path(path_str)
    
    with patch('src.spotify.playlist_downloader.Path', side_effect=mock_path_constructor):
        tracks = [{'name': 'Test Track'}]
        
        result = save_tracks_to_json(
            tracks,
            'Test Playlist',
            mock_user_info,
            'playlist123',
            'https://spotify.com/playlist/123'
        )
        
        # Check if file exists and content is correct
        saved_file = bronze_dir / 'test_playlist.json'
        assert saved_file.exists()
        
        content = json.loads(saved_file.read_text())
        assert content['playlist_name'] == 'Test Playlist'
        assert content['playlist_id'] == 'playlist123'
        assert content['tracks'] == tracks

def test_process_track_batch(mock_track):
    """Test processing a batch of tracks"""
    batch = {
        'items': [
            {'track': mock_track, 'added_at': '2024-03-19T12:00:00Z'},
            {'track': None},  # Should be skipped
            {'track': mock_track, 'added_at': '2024-03-19T12:01:00Z'}
        ]
    }
    
    results = list(process_track_batch(batch))
    assert len(results) == 2
    assert all(track['name'] == 'Test Track' for track in results) 