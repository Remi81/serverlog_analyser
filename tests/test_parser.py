import asyncio
import json
import pathlib
import os

from serverlog_analyser.parser import LogParser


def write_tmp(lines, name="tmp.log"):
    p = pathlib.Path(name)
    p.write_text("\n".join(lines))
    return p


def test_ip_extraction_date_first(tmp_path):
    p = tmp_path / "date_first.log"
    lines = [
        '2026-01-23 12:00:01 192.0.2.10 - - "GET /a HTTP/1.1" 200 123 0.11',
        '2026-01-23 12:00:02 192.0.2.11 - - "GET /b HTTP/1.1" 200 123 0.12',
        '2026-01-23 12:00:03 192.0.2.10 - - "GET /a HTTP/1.1" 200 123 0.13',
    ]
    p.write_text("\n".join(lines))

    res = asyncio.run(LogParser.parse_file(str(p)))
    assert ('192.0.2.10', 2) in res['top_ips']
    assert ('192.0.2.11', 1) in res['top_ips']


def test_aggregated_paths_counts(tmp_path):
    p = tmp_path / "aides.log"
    lines = [
        '127.0.0.1 - - "GET /aides/?page=1&perimeter=1 HTTP/1.1" 200 12 0.1',
        '127.0.0.2 - - "GET /aides/?page=2&perimeter=1 HTTP/1.1" 200 12 0.2',
        '127.0.0.3 - - "GET /aides/exporter/?perimeter=1 HTTP/1.1" 200 12 0.1',
    ]
    p.write_text("\n".join(lines))

    res = asyncio.run(LogParser.parse_file(str(p)))
    agg = dict(res.get('top_paths_aggregated', []))
    assert agg.get('/aides') == 2
    assert agg.get('/aides/exporter') == 1


def test_timings_calculation(tmp_path):
    p = tmp_path / "timings.log"
    lines = [
        '127.0.0.1 - - "GET /x HTTP/1.1" 200 12 0.1',
        '127.0.0.1 - - "GET /x HTTP/1.1" 200 12 0.3',
        '127.0.0.1 - - "GET /x HTTP/1.1" 200 12 0.2',
    ]
    p.write_text("\n".join(lines))

    res = asyncio.run(LogParser.parse_file(str(p)))
    timings = res['timings']
    assert timings['min'] == 0.1
    assert round(timings['mean'], 6) == round((0.1 + 0.2 + 0.3) / 3, 6)
    assert timings['median'] == 0.2
