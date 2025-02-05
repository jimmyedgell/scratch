"""
Spotify Playlist CSV Converter

This module converts downloaded playlist JSON files to a combined CSV format.
Reads from data/bronze directory and writes to data/silver directory.

Created: 2025-02-04
Author: James Edgell
Version: 0.0.1
License: MIT

Version History
--------------
0.0.1 (2025-02-05)
    - Fixed test suite
    - Added proper error handling
    - Improved logging

0.0.0 (2025-02-04)
    - Initial implementation
"""

# Standard imports
import json
import logging
from pathlib import Path

# Third party imports
import pandas as pd


# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def format_duration(ms: int) -> str:
    """
    Convert milliseconds to a human-readable duration string.

    Parameters
    ----------
    ms : int
        Duration in milliseconds.

    Returns
    -------
    str
        Formatted duration string (MM:SS).
    """
    seconds = ms // 1000
    minutes = seconds // 60
    remaining_seconds = seconds % 60
    return f"{minutes}:{remaining_seconds:02d}"

def combine_playlists_to_csv() -> Path:
    """
    Combine all downloaded playlist JSON files into a single CSV file.
    
    Returns
    -------
    Path
        Path to the generated CSV file.
    
    Notes
    -----
    - Reads JSON files from data/bronze directory
    - Writes combined CSV to data/silver directory
    - Formats durations as MM:SS
    - Adds playlist name to each track
    """
    logger.info("Starting playlist combination process...")
    
    # Setup paths
    bronze_dir = Path('data/bronze')
    silver_dir = Path('data/silver')
    silver_dir.mkdir(parents=True, exist_ok=True)
    
    if not bronze_dir.exists():
        raise FileNotFoundError("No bronze directory found. Please download playlists first.")
    
    # Read all JSON files
    all_tracks = []
    json_files = list(bronze_dir.glob('*.json'))
    
    if not json_files:
        raise FileNotFoundError("No playlist files found in bronze directory.")
    
    logger.info(f"Found {len(json_files)} playlist files to process.")
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                playlist_data = json.load(f)
                
            playlist_name = playlist_data['playlist_name']
            tracks = playlist_data['tracks']
            
            # Add playlist name to each track
            for track in tracks:
                track['playlist'] = playlist_name
                track['duration'] = format_duration(track['duration_ms'])
            
            all_tracks.extend(tracks)
            logger.info(f"Processed {playlist_name} ({len(tracks)} tracks)")
            
        except Exception as e:
            logger.error(f"Error processing {json_file.name}: {e}")
            continue
    
    if not all_tracks:
        raise ValueError("No tracks were found in the playlist files.")
    
    # Convert to DataFrame and save
    df = pd.DataFrame(all_tracks)
    
    # Reorder columns to put playlist first
    columns = ['playlist'] + [col for col in df.columns if col != 'playlist']
    df = df[columns]
    
    # Save to CSV
    output_file = silver_dir / 'combined_playlists.csv'
    df.to_csv(output_file, index=False, encoding='utf-8')
    
    logger.info(f"Successfully combined {len(all_tracks)} tracks from {len(json_files)} playlists.")
    logger.info(f"Output saved to: {output_file}")
    
    return output_file

def main():
    """Main entry point for the script."""
    try:
        logger.info("Starting playlist CSV conversion...")
        combine_playlists_to_csv()
        logger.info("Conversion completed successfully.")
    except FileNotFoundError as e:
        logger.error(f"File error: {e}")
        logger.info("Please run playlist_downloader.py first to download your playlists.")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise

if __name__ == '__main__':
    main() 