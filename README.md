# Personal Projects Repository

A collection of various personal projects and experiments.

## Projects

### Spotify Playlist Manager
- Download and manage Spotify playlists
- Convert playlist data between formats
- [More details](./docs/spotify/README.md)

## Repository Structure

```
project_root/
├── conf/          # Configuration files
├── data/          # Data storage
│   ├── bronze/    # Raw data
│   ├── silver/    # Processed data
│   └── gold/      # Final processed data
├── src/           # Source code for all projects
├── tests/         # Test suites
├── notebooks/     # Jupyter notebooks
└── docs/          # Project-specific documentation
```

## Getting Started

1. Clone the repository

2. Install uv:
   - Windows: Download from https://github.com/astral-sh/uv/releases
   - Unix/MacOS: `curl -LsSf https://astral.sh/uv/install.sh | sh`

3. Create and activate a virtual environment:
```
uv venv
# Activate the environment using your shell's activate command
```

4. Install dependencies:
```
# Install project dependencies only
uv pip install ./src/{project}

# Or install with development dependencies
uv pip install -e "./src/{project}[dev]"
```

## Development

### Running Tests
```
cd src/{project}
pytest ../../tests/{project}/ -v
```

### Code Style
This repository follows PEP 8 guidelines. Each project includes development dependencies for code formatting and linting (black, ruff, mypy).

## Version History

### 0.0.1 (2025-02-05)
- Fix test_playlist_converter.py in Spotify Playlist Manager.

### 0.0.0 (2025-02-04)
- Initial implementation of Spotify Playlist Manager.

## License

MIT

## Author

James Edgell (2024)