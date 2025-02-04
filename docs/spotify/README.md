# Spotify Playlist Manager

A Python package for managing Spotify playlists, including downloading and format conversion.


## Features

- Download your Spotify playlists to JSON format
- Convert playlist data to CSV format with proper duration formatting
- Filter out specific playlist types (e.g., Podcasts, Audiobooks)
- Track-level information including names, artists, albums, and timestamps


## Configuration

Create a `conf/conf_local.json` file with your Spotify API credentials:
```json
{
  "SPOTIFY": {
    "CLIENT_ID": "your_client_id",
    "CLIENT_SECRET": "your_client_secret"
  }
}
```

## Usage Examples

### Downloading Playlists

```python
from src.spotify import download_my_playlists

# Downloads all your playlists (excluding Pods and Audiobooks)
download_my_playlists()
```

### Converting to CSV

```python
from src.spotify import combine_playlists_to_csv

# Combines all downloaded playlists into a single CSV
combine_playlists_to_csv()
```

## Data Structure

The project uses a medallion architecture for data organization:
- `bronze/`: Raw JSON data from Spotify API
- `silver/`: Processed CSV data with standardized formats
- `gold/`: Final processed data (if needed)


## Version History

### 0.0.0 (2024-03-19)
- Initial implementation
- Core features:
  - Download playlists and liked songs
  - Convert to JSON format
  - Pagination support
  - UTF-8 encoding
  - Proper error handling
- Known limitations:
  - Only downloads user-created playlists
  - Skips podcasts and audiobooks


## Author

James Edgell (2024) 