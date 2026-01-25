"""Module parser: parsing et calcul statistique des logs."""
import re
import os
import asyncio
from collections import Counter
import statistics
from typing import List, Dict, Any, Optional
import aiofiles

class LogParser:
    pattern = re.compile(r"^(?P<ip>\S+) .* \"(?P<method>\S+) (?P<path>\S+) .*\" (?P<status>\d{3}) (?P<size>\S+)(?: (?P<duration>\d+(?:\.\d+)?))?.*$")

    @staticmethod
    async def parse_file(path: str, progress_callback=None, should_cancel=None) -> Dict[str, Any]:
        total = 0
        status_counts = Counter()
        paths = Counter()
        ips = Counter()
        # aggregated paths without query/fragments (useful to group /aides/?page=1 etc.)
        norm_paths = Counter()
        durations: List[float] = []

        total_bytes = 0
        try:
            total_bytes = os.path.getsize(path)
        except Exception:
            total_bytes = 0
        bytes_read = 0
        last_reported = 0.0

        async with aiofiles.open(path, "r") as f:
            async for line in f:
                # cancellation
                try:
                    if should_cancel and should_cancel():
                        raise asyncio.CancelledError()
                except asyncio.CancelledError:
                    raise
                except Exception:
                    pass

                total += 1
                try:
                    bytes_read += len(line.encode("utf-8"))
                except Exception:
                    bytes_read += len(line)

                m = LogParser.pattern.match(line)
                if not m:
                    continue
                # sometimes logs put a timestamp or other token first instead of the IP
                # try to use the captured ip if it looks like an IPv4 address, otherwise search the line
                ip = m.group("ip")
                if not re.match(r'^(?:\d{1,3}\.){3}\d{1,3}$', ip):
                    search = re.search(r'(?P<ipv4>(?:\d{1,3}\.){3}\d{1,3})', line)
                    if search:
                        ip = search.group('ipv4')
                status = m.group("status")
                status_counts[status] += 1
                raw_path = m.group("path")
                paths[raw_path] += 1
                # normalize path for aggregation (strip query string and fragment, remove trailing slash)
                norm = raw_path.split('?')[0].split('#')[0]
                if norm != '/' and norm.endswith('/'):
                    norm = norm[:-1]
                norm_paths[norm] += 1
                ips[ip] += 1
                d = m.group("duration")
                if d:
                    try:
                        durations.append(float(d))
                    except ValueError:
                        pass

                if total_bytes > 0:
                    progress = min(0.99, bytes_read / total_bytes)
                else:
                    progress = min(0.99, total / 100000)

                if progress_callback and (progress - last_reported >= 0.01 or total % 200 == 0):
                    last_reported = progress
                    try:
                        progress_callback({
                            "progress": progress,
                            "bytes_read": bytes_read,
                            "lines_parsed": total,
                        })
                    except Exception:
                        pass

        timings = {
            "min": min(durations) if durations else 0,
            "mean": statistics.mean(durations) if durations else 0,
            "median": statistics.median(durations) if durations else 0,
            "p95": (sorted(durations)[int(0.95 * len(durations))] if durations else 0),
            "p99": (sorted(durations)[int(0.99 * len(durations))] if durations else 0),
        }

        if progress_callback:
            try:
                progress_callback({"progress": 0.999, "bytes_read": bytes_read, "lines_parsed": total})
            except Exception:
                pass

        # Also provide aggregated paths (without query strings) to surface logical roots such as /aides
        aggregated = norm_paths.most_common(200)

        return {
            "total_requests": total,
            "status_counts": dict(status_counts),
            "top_paths": paths.most_common(20),
            "top_paths_aggregated": aggregated,
            "top_ips": ips.most_common(20),
            "timings": timings,
        }