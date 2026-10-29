"""Record actual Release asset counters; never download asset contents."""
import csv
import io
import json
import os
from pathlib import Path
import sys
import tempfile
from datetime import datetime, timezone, timedelta
from urllib.parse import quote
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ["date_jst", "fetched_at", "release_tag", "asset_name", "download_count", "increase"]
JST = timezone(timedelta(hours=9))


def merge_rows(rows, observations, now):
    timestamp = now.astimezone(JST).isoformat(timespec="seconds")
    day = now.astimezone(JST).date().isoformat()
    indexed = {}
    for row in rows:
        key = (row["date_jst"], row["release_tag"], row["asset_name"])
        if key in indexed:
            raise ValueError(f"Duplicate existing record: {key}")
        indexed[key] = dict(row)
    for tag, name, count in observations:
        if type(count) is not int or count < 0:
            raise ValueError("Invalid download_count")
        key = (day, tag, name)
        previous = indexed.get(key)
        if previous and previous["fetched_at"] > timestamp:
            raise ValueError("Observation older than saved record")
        if previous and count < int(previous["download_count"]):
            raise ValueError("Counter decreased since today's saved observation")
        indexed[key] = dict(zip(FIELDS, [day, timestamp, tag, name, str(count), ""]))
    result = sorted(indexed.values(), key=lambda r: (r["date_jst"], r["release_tag"], r["asset_name"]))
    last = {}
    for row in result:
        key = (row["release_tag"], row["asset_name"])
        count = int(row["download_count"])
        if key in last and count < last[key]:
            raise ValueError(f"Counter decreased for {key}; investigate asset replacement/reset")
        row["increase"] = str(count - last[key]) if key in last else ""
        last[key] = count
    return result


def main():
    repository = os.environ.get("GITHUB_REPOSITORY", "miyama31/kotsubu-tips-electronics")
    targets = json.loads((ROOT / "config/download-targets.json").read_text(encoding="utf-8"))
    if not targets or len({(t["release_tag"], t["asset_name"]) for t in targets}) != len(targets):
        raise ValueError("Targets must be nonempty and unique")
    observations = []
    headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "kotsubu-download-history"}
    if os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]
    for target in targets:
        tag, name = target["release_tag"], target["asset_name"]
        url = f"https://api.github.com/repos/{repository}/releases/tags/{quote(tag, safe='')}"
        with urlopen(Request(url, headers=headers), timeout=60) as response:
            release = json.load(response)
        if release.get("draft") or release.get("prerelease"):
            raise ValueError(f"Expected published normal release: {tag}")
        matches = [a for a in release["assets"] if a["name"] == name and a["state"] == "uploaded"]
        if len(matches) != 1:
            raise ValueError(f"Expected exactly one uploaded asset: {tag}/{name}")
        observations.append((tag, name, matches[0]["download_count"]))
    path = ROOT / "data/download-history.csv"
    rows = []
    if path.exists():
        with path.open(encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream)
            if reader.fieldnames != FIELDS:
                raise ValueError("Unexpected CSV columns")
            rows = list(reader)
    result = merge_rows(rows, observations, datetime.now(JST))
    path.parent.mkdir(exist_ok=True)
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(result)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="", dir=path.parent, delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(buffer.getvalue())
    try:
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
    print(buffer.getvalue())


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"::error::Download history recording failed: {error}", file=sys.stderr)
        sys.exit(1)
