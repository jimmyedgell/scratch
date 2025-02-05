"""
Spotify Playlist Downloader

This module handles downloading playlists and liked songs from Spotify.
Each playlist is saved as a separate JSON file in the data/bronze directory.

Created: 2025-02-04
Author: James Edgell
Version: 0.0.1
License: MIT

Version History
--------------
0.0.0 (2025-02-04)
    - Initial implementation
    - Download playlists and liked songs
    - Save to JSON with proper UTF-8 encoding
    - Pagination support for large playlists
    - Logging and error handling
"""

# Standard imports
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Iterator

# Third party imports
import spotipy
from spotipy.oauth2 import SpotifyOAuth


# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_config() -> Dict:
    """
    Load configuration from conf_local.json file.

    Returns
    -------
    Dict
        Dictionary containing configuration data with Spotify credentials.

    Raises
    ------
    FileNotFoundError
        If conf_local.json is not found in the conf directory.
    json.JSONDecodeError
        If the configuration file contains invalid JSON.

    Examples
    --------
    >>> config = load_config()
    >>> spotify_config = config.get('SPOTIFY', {})
    >>> client_id = spotify_config.get('CLIENT_ID')
    """
    config_path = Path('conf/conf_local.json')
    if not config_path.exists():
        raise FileNotFoundError("conf_local.json not found! Please create it with your Spotify credentials.")
    
    with open(config_path, 'r') as f:
        return json.load(f)

def get_spotify_client() -> spotipy.Spotify:
    """
    Initialize and return an authenticated Spotify client.

    Returns
    -------
    spotipy.Spotify
        Authenticated Spotify client instance.

    Raises
    ------
    ValueError
        If Spotify credentials are missing from the configuration.
    spotipy.SpotifyOauthError
        If authentication with Spotify fails.

    Notes
    -----
    Requires valid Spotify API credentials in conf_local.json.
    Uses OAuth2 for authentication with the following scopes:
    - playlist-read-private
    - playlist-read-collaborative
    - user-library-read
    - user-read-private
    """
    config = load_config()
    spotify_config = config.get('SPOTIFY', {})
    
    if not all([spotify_config.get('CLIENT_ID'), spotify_config.get('CLIENT_SECRET')]):
        raise ValueError("Missing Spotify credentials in conf_local.json")
    
    return spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=spotify_config.get('CLIENT_ID'),
        client_secret=spotify_config.get('CLIENT_SECRET'),
        redirect_uri='http://localhost:8888/callback',
        scope='playlist-read-private playlist-read-collaborative user-library-read user-read-private'
    ))

def sanitize_filename(name: str) -> str:
    """
    Convert a string into a safe filename by removing or replacing invalid characters.

    Parameters
    ----------
    name : str
        The original filename to sanitize.

    Returns
    -------
    str
        A sanitized filename safe for use on most filesystems.

    Examples
    --------
    >>> sanitize_filename("Hello World!")
    'hello_world'
    >>> sanitize_filename("My Playlist #1")
    'my_playlist_1'
    """
    import re
    safe_name = re.sub(r'[^\w\s-]', '_', name)
    safe_name = re.sub(r'_+', '_', safe_name.replace(' ', '_'))
    return safe_name.lower().strip('_')

def extract_track_info(track: Dict, added_at: str) -> Optional[Dict]:
    """
    Extract relevant track information from Spotify track object.

    Parameters
    ----------
    track : Dict
        Spotify track object containing track metadata.
    added_at : str
        ISO 8601 timestamp when the track was added.

    Returns
    -------
    Optional[Dict]
        Dictionary containing extracted track information or None if extraction fails.
        Keys include: name, artist, album, duration_ms, spotify_url, added_at.

    Notes
    -----
    Returns None if any required fields are missing from the track object.
    """
    try:
        return {
            'name': track['name'],
            'artist': track['artists'][0]['name'],
            'album': track['album']['name'],
            'duration_ms': track['duration_ms'],
            'spotify_url': track['external_urls']['spotify'],
            'added_at': added_at
        }
    except KeyError as e:
        logger.warning(f"Missing key in track data: {e}")
        return None

def save_tracks_to_json(
    tracks: List[Dict],
    playlist_name: str,
    user_info: Dict,
    playlist_id: Optional[str] = None,
    playlist_url: Optional[str] = None
) -> Path:
    """
    Save track information to a JSON file.

    Parameters
    ----------
    tracks : List[Dict]
        List of track information dictionaries to save.
    playlist_name : str
        Name of the playlist.
    user_info : Dict
        Dictionary containing user information (id, display_name).
    playlist_id : Optional[str], optional
        Spotify playlist ID, by default None.
    playlist_url : Optional[str], optional
        Spotify playlist URL, by default None.

    Returns
    -------
    Path
        Path object pointing to the saved JSON file.

    Notes
    -----
    Creates the data/bronze directory if it doesn't exist.
    Files are saved with sanitized names in UTF-8 encoding.
    """
    output_dir = Path('data/bronze')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    safe_filename = sanitize_filename(playlist_name)
    output_file = output_dir / f"{safe_filename}.json"
    
    data = {
        'playlist_name': playlist_name,
        'playlist_id': playlist_id,
        'playlist_owner': user_info['display_name'],
        'owner_id': user_info['id'],
        'total_tracks': len(tracks),
        'playlist_url': playlist_url,
        'tracks': tracks
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    return output_file

def process_track_batch(batch: Dict) -> Iterator[Dict]:
    """
    Process a batch of tracks from Spotify API response.

    Parameters
    ----------
    batch : Dict
        Spotify API response containing a batch of tracks.

    Yields
    ------
    Dict
        Processed track information for each valid track in the batch.

    Notes
    -----
    Skips tracks that are None or have missing required information.
    """
    for item in batch['items']:
        if item.get('track'):
            track_info = extract_track_info(item['track'], item['added_at'])
            if track_info:
                yield track_info

def download_liked_songs(sp: spotipy.Spotify, user_info: Dict) -> List[Dict]:
    """
    Download user's Liked Songs from Spotify.

    Parameters
    ----------
    sp : spotipy.Spotify
        Authenticated Spotify client instance.
    user_info : Dict
        Dictionary containing user information.

    Returns
    -------
    List[Dict]
        List of track information dictionaries for all liked songs.

    Notes
    -----
    Uses pagination to handle large libraries (50 tracks per request).
    Saves the downloaded tracks to data/bronze/liked_songs.json.
    """
    logger.info("Processing Liked Songs")
    tracks = []
    offset = 0
    limit = 50  # Spotify's maximum limit per request
    
    while True:
        try:
            results = sp.current_user_saved_tracks(limit=limit, offset=offset)
            if not results['items']:
                break
                
            new_tracks = list(process_track_batch(results))
            tracks.extend(new_tracks)
            logger.info(f"Processed {len(tracks)} liked songs so far...")
            
            if len(new_tracks) < limit:
                break
                
            offset += limit
            
        except Exception as e:
            logger.error(f"Error downloading liked songs: {e}")
            break
    
    if tracks:
        output_file = save_tracks_to_json(tracks, 'Liked Songs', user_info)
        logger.info(f"Successfully downloaded {len(tracks)} Liked Songs to {output_file}")
    else:
        logger.warning("No liked songs were downloaded")
    
    return tracks

def download_playlist(
    sp: spotipy.Spotify,
    playlist: Dict,
    user_info: Dict
) -> Optional[List[Dict]]:
    """
    Download a single playlist's tracks from Spotify.

    Parameters
    ----------
    sp : spotipy.Spotify
        Authenticated Spotify client instance.
    playlist : Dict
        Playlist information dictionary from Spotify API.
    user_info : Dict
        Dictionary containing user information.

    Returns
    -------
    Optional[List[Dict]]
        List of track information dictionaries if successful, None if playlist is skipped.

    Notes
    -----
    Skips playlists that:
    - Start with 'Pods' or 'Audiobooks'
    - Are not created by the user
    Uses pagination to handle large playlists (100 tracks per request).
    """
    playlist_name = playlist['name']
    
    if playlist_name.startswith(('Pods', 'Audiobooks')):
        logger.info(f"Skipping podcast/audiobook playlist: {playlist_name}")
        return None
    
    if playlist['owner']['id'] != user_info['id']:
        logger.info(f"Skipping non-user playlist: {playlist_name}")
        return None
    
    logger.info(f"Processing playlist: {playlist_name}")
    tracks = []
    offset = 0
    limit = 100
    
    while True:
        try:
            track_results = sp.playlist_tracks(
                playlist['id'],
                limit=limit,
                offset=offset
            )
            
            if not track_results['items']:
                break
                
            new_tracks = list(process_track_batch(track_results))
            tracks.extend(new_tracks)
            logger.info(f"Processed {len(tracks)} tracks in '{playlist_name}' so far...")
            
            if len(new_tracks) < limit:
                break
                
            offset += limit
            
        except Exception as e:
            logger.error(f"Error downloading playlist {playlist_name}: {e}")
            break
    
    if tracks:
        output_file = save_tracks_to_json(
            tracks,
            playlist_name,
            user_info,
            playlist['id'],
            playlist['external_urls'].get('spotify')
        )
        logger.info(f"Successfully downloaded playlist '{playlist_name}' ({len(tracks)} tracks) to {output_file}")
    else:
        logger.warning(f"No tracks were downloaded for playlist: {playlist_name}")
    
    return tracks

def download_my_playlists() -> Dict[str, Optional[List[Dict]]]:
    """
    Download all playlists created by the user (including Liked Songs).

    Returns
    -------
    Dict[str, Optional[List[Dict]]]
        Dictionary mapping playlist names to their track lists.
        None values indicate skipped playlists.

    Notes
    -----
    Downloads in this order:
    1. User's Liked Songs
    2. User-created playlists (excluding podcasts and audiobooks)
    
    Uses pagination to handle large numbers of playlists (50 per request).
    Saves each playlist to a separate JSON file in data/bronze/.
    """
    try:
        sp = get_spotify_client()
        user_info = sp.current_user()
        results_dict = {}
        playlists_processed = 0
        
        liked_songs = download_liked_songs(sp, user_info)
        if liked_songs:
            results_dict['Liked Songs'] = liked_songs
            playlists_processed += 1
        
        offset = 0
        limit = 50
        
        while True:
            try:
                results = sp.current_user_playlists(limit=limit, offset=offset)
                if not results['items']:
                    break
                
                for playlist in results['items']:
                    tracks = download_playlist(sp, playlist, user_info)
                    if tracks is not None:
                        results_dict[playlist['name']] = tracks
                        playlists_processed += 1
                
                if len(results['items']) < limit:
                    break
                    
                offset += limit
                
            except Exception as e:
                logger.error(f"Error processing playlists batch: {e}")
                break
        
        logger.info(f"\nDownload complete! Processed {playlists_processed} playlists (including Liked Songs).")
        return results_dict
        
    except Exception as e:
        logger.error(f"Fatal error in download_my_playlists: {e}")
        raise

def main():
    """
    Main entry point for the script.

    Notes
    -----
    Handles the main execution flow and error reporting:
    - Initializes the download process
    - Catches and logs configuration errors
    - Provides user-friendly error messages
    """
    try:
        logger.info("Starting Spotify playlist download...")
        download_my_playlists()
        logger.info("Download process completed successfully.")
    except FileNotFoundError as e:
        logger.error(f"Configuration error: {e}")
        logger.info("Please create conf/conf_local.json with your Spotify credentials.")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise

if __name__ == '__main__':
    main() 