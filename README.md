# IPTV Stream Checker

A lightweight Python tool to check IPTV stream health, response times, and playlist validity.

## Features

- Parse M3U/M3U8 playlists and validate stream URLs
- Check stream availability and response time
- Export results to CSV or JSON
- Support for HTTP, HTTPS, and RTMP streams
- Configurable timeout and retry settings

## Installation

```bash
git clone https://github.com/lindakumar320/iptv-stream-checker-b8f724.git
cd iptv-stream-checker-b8f724
pip install -r requirements.txt
```

## Usage

```python
from stream_checker import StreamChecker

checker = StreamChecker(timeout=10, retries=3)
results = checker.check_playlist("playlist.m3u")

for stream in results:
    print(f"{stream['name']}: {stream['status']} ({stream['response_ms']}ms)")
```

### Command Line

```bash
python check_streams.py --input playlist.m3u --output results.csv
python check_streams.py --url "http://example.com/playlist.m3u8" --format json
```

## Configuration

Create a `config.yaml` file:

```yaml
timeout: 10
retries: 3
concurrent_checks: 5
output_format: csv
```

## Requirements

- Python 3.8+
- requests
- aiohttp
- pyyaml

## Related Resources

If you're looking for recommendations on the best streaming and IPTV applications available in 2026, check out this comprehensive guide on [best IPTV apps](https://xtreamcode.tv/blog/best-iptv-apps-2026) — it covers setup, features, and device compatibility.

## License

MIT License — see [LICENSE](LICENSE) for details.

## Contributing

Pull requests welcome. Please open an issue first to discuss proposed changes.
