#!/usr/bin/env python3
"""IPTV Stream Checker — check playlist health and stream availability."""

import argparse
import csv
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import requests
import yaml


@dataclass
class StreamResult:
    name: str
    url: str
    status: str = "unknown"
    response_ms: float = 0.0
    error: Optional[str] = None


class StreamChecker:
    """Check IPTV stream health from M3U/M3U8 playlists."""

    def __init__(self, timeout: int = 10, retries: int = 3, concurrent: int = 5):
        self.timeout = timeout
        self.retries = retries
        self.concurrent = concurrent

    def parse_m3u(self, content: str) -> list[dict]:
        """Parse M3U/M3U8 playlist content into stream entries."""
        streams = []
        lines = content.strip().split("\n")
        current_name = ""

        for line in lines:
            line = line.strip()
            if line.startswith("#EXTINF:"):
                # Extract channel name from EXTINF line
                match = line.split(",", 1)
                current_name = match[1].strip() if len(match) > 1 else "Unknown"
            elif line and not line.startswith("#"):
                streams.append({"name": current_name or "Unknown", "url": line})
                current_name = ""

        return streams

    def check_stream(self, name: str, url: str) -> StreamResult:
        """Check if a single stream URL is accessible."""
        result = StreamResult(name=name, url=url)

        for attempt in range(self.retries):
            try:
                start = time.monotonic()
                resp = requests.head(
                    url, timeout=self.timeout, allow_redirects=True,
                    headers={"User-Agent": "IPTV-Checker/1.0"}
                )
                elapsed = (time.monotonic() - start) * 1000

                if resp.status_code < 400:
                    result.status = "online"
                    result.response_ms = round(elapsed, 1)
                    return result
                else:
                    result.status = "error"
                    result.error = f"HTTP {resp.status_code}"

            except requests.Timeout:
                result.status = "timeout"
                result.error = "Connection timed out"
            except requests.ConnectionError as e:
                result.status = "offline"
                result.error = str(e)[:100]
            except Exception as e:
                result.status = "error"
                result.error = str(e)[:100]

        return result

    def check_playlist(self, source: str) -> list[StreamResult]:
        """Check all streams in a playlist file or URL."""
        if source.startswith(("http://", "https://")):
            resp = requests.get(source, timeout=self.timeout)
            content = resp.text
        else:
            content = Path(source).read_text()

        streams = self.parse_m3u(content)
        results = []

        with ThreadPoolExecutor(max_workers=self.concurrent) as pool:
            futures = {
                pool.submit(self.check_stream, s["name"], s["url"]): s
                for s in streams
            }
            for future in as_completed(futures):
                results.append(future.result())

        return sorted(results, key=lambda r: r.name)


def export_results(results: list[StreamResult], output: str, fmt: str = "csv"):
    """Export check results to file."""
    if fmt == "json":
        data = [{"name": r.name, "url": r.url, "status": r.status,
                 "response_ms": r.response_ms, "error": r.error} for r in results]
        Path(output).write_text(json.dumps(data, indent=2))
    else:
        with open(output, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Name", "URL", "Status", "Response (ms)", "Error"])
            for r in results:
                writer.writerow([r.name, r.url, r.status, r.response_ms, r.error or ""])


def main():
    parser = argparse.ArgumentParser(description="Check IPTV stream health")
    parser.add_argument("--input", "-i", help="M3U playlist file path")
    parser.add_argument("--url", "-u", help="M3U playlist URL")
    parser.add_argument("--output", "-o", help="Output file path")
    parser.add_argument("--format", "-f", choices=["csv", "json"], default="csv")
    parser.add_argument("--timeout", "-t", type=int, default=10)
    parser.add_argument("--retries", "-r", type=int, default=3)
    args = parser.parse_args()

    source = args.url or args.input
    if not source:
        parser.error("Provide --input or --url")

    checker = StreamChecker(timeout=args.timeout, retries=args.retries)
    results = checker.check_playlist(source)

    online = sum(1 for r in results if r.status == "online")
    print(f"\nChecked {len(results)} streams: {online} online, {len(results) - online} issues")

    for r in results:
        icon = "✓" if r.status == "online" else "✗"
        print(f"  {icon} {r.name}: {r.status} ({r.response_ms}ms)")

    if args.output:
        export_results(results, args.output, args.format)
        print(f"\nResults saved to {args.output}")


if __name__ == "__main__":
    main()
