#!/usr/bin/env python3
"""
Find duplicate files in a directory by SHA-256 content hash.

Usage:
    python3 find_duplicates.py <directory> [--no-recurse]

Outputs JSON to stdout with duplicate groups, file metadata, and summary stats.
"""

import hashlib
import json
import os
import sys
from collections import defaultdict


def hash_file(filepath, chunk_size=8192):
    """Compute SHA-256 hash of a file, reading in chunks for memory efficiency."""
    sha256 = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                sha256.update(chunk)
        return sha256.hexdigest()
    except (PermissionError, OSError) as e:
        return None, str(e)


def scan_directory(directory, recurse=True):
    """Scan a directory and return file paths with metadata."""
    files = []
    errors = []

    if recurse:
        for root, dirs, filenames in os.walk(directory):
            for filename in filenames:
                filepath = os.path.join(root, filename)
                if os.path.islink(filepath):
                    continue
                try:
                    stat = os.stat(filepath)
                    files.append({
                        "path": filepath,
                        "size": stat.st_size,
                        "modified": stat.st_mtime,
                    })
                except (PermissionError, OSError) as e:
                    errors.append({"path": filepath, "error": str(e)})
    else:
        for entry in os.scandir(directory):
            if entry.is_file(follow_symlinks=False):
                try:
                    stat = entry.stat()
                    files.append({
                        "path": entry.path,
                        "size": stat.st_size,
                        "modified": stat.st_mtime,
                    })
                except (PermissionError, OSError) as e:
                    errors.append({"path": entry.path, "error": str(e)})

    return files, errors


def find_duplicates(directory, recurse=True):
    """Find duplicate files by content hash. Returns JSON-serializable dict."""
    if not os.path.isdir(directory):
        return {"error": f"'{directory}' is not a valid directory."}

    files, scan_errors = scan_directory(directory, recurse)

    if not files:
        return {
            "scan_path": os.path.abspath(directory),
            "total_files_scanned": 0,
            "duplicate_groups": [],
            "total_duplicate_files": 0,
            "total_wasted_bytes": 0,
            "errors": scan_errors,
        }

    # Group by file size first (quick pre-filter — files with unique sizes can't be duplicates)
    size_groups = defaultdict(list)
    for f in files:
        size_groups[f["size"]].append(f)

    # Only hash files that share a size with at least one other file
    hash_groups = defaultdict(list)
    hash_errors = []

    for size, group in size_groups.items():
        if len(group) < 2:
            continue
        for f in group:
            result = hash_file(f["path"])
            if isinstance(result, tuple):
                # Error case
                hash_errors.append({"path": f["path"], "error": result[1]})
                continue
            hash_groups[result].append(f)

    # Filter to only groups with actual duplicates
    duplicate_groups = []
    total_duplicate_files = 0
    total_wasted_bytes = 0

    for file_hash, group in sorted(hash_groups.items(), key=lambda x: -x[1][0]["size"]):
        if len(group) < 2:
            continue

        # Sort by modification time (oldest first)
        group.sort(key=lambda f: f["modified"])

        duplicate_groups.append({
            "hash": file_hash,
            "size_bytes": group[0]["size"],
            "files": [
                {
                    "path": f["path"],
                    "modified": f["modified"],
                }
                for f in group
            ],
        })

        # Wasted space = (copies - 1) * file_size
        total_duplicate_files += len(group) - 1
        total_wasted_bytes += (len(group) - 1) * group[0]["size"]

    return {
        "scan_path": os.path.abspath(directory),
        "total_files_scanned": len(files),
        "duplicate_groups": duplicate_groups,
        "total_duplicate_files": total_duplicate_files,
        "total_wasted_bytes": total_wasted_bytes,
        "errors": scan_errors + hash_errors,
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 find_duplicates.py <directory> [--no-recurse]", file=sys.stderr)
        sys.exit(1)

    directory = sys.argv[1]
    recurse = "--no-recurse" not in sys.argv

    result = find_duplicates(directory, recurse)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
