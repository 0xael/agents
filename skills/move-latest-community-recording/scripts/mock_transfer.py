#!/usr/bin/env python3
"""
Mock version of transfer_recording.py for testing.
Simulates Microsoft Graph API responses without requiring real credentials.

Set MOCK_MODE=1 to use this instead of real API calls.
"""

import argparse
import json
import os
import sys
import time

DEFAULT_SEARCH = "BTP Security Community"

MOCK_RECORDINGS = [
    {
        "id": "mock-id-001",
        "name": "BTP Security Community - 2026-03-07 - Monthly Call.mp4",
        "size": 524288000,  # 500 MB
        "lastModifiedDateTime": "2026-03-07T14:30:00Z",
        "file": {"mimeType": "video/mp4"},
    },
    {
        "id": "mock-id-002",
        "name": "BTP Security Community - 2026-02-07 - Monthly Call.mp4",
        "size": 483901440,  # 461 MB
        "lastModifiedDateTime": "2026-02-07T14:30:00Z",
        "file": {"mimeType": "video/mp4"},
    },
    {
        "id": "mock-id-003",
        "name": "BTP Security Community - 2026-01-10 - Quarterly Review.mp4",
        "size": 734003200,  # 700 MB
        "lastModifiedDateTime": "2026-01-10T15:00:00Z",
        "file": {"mimeType": "video/mp4"},
    },
]


def fmt_size(bytes_val):
    if bytes_val >= 1024 * 1024 * 1024:
        return f"{bytes_val / 1024 / 1024 / 1024:.1f} GB"
    if bytes_val >= 1024 * 1024:
        return f"{bytes_val / 1024 / 1024:.1f} MB"
    if bytes_val >= 1024:
        return f"{bytes_val / 1024:.1f} KB"
    return f"{bytes_val} bytes"


def check_env():
    token = os.environ.get("MS_GRAPH_TOKEN", "")
    site_url = os.environ.get("MS_SHAREPOINT_SITE_URL", "")
    library = os.environ.get("MS_SHAREPOINT_LIBRARY", "")

    missing = []
    if not token:
        missing.append("MS_GRAPH_TOKEN")
    if not site_url:
        missing.append("MS_SHAREPOINT_SITE_URL")
    if not library:
        missing.append("MS_SHAREPOINT_LIBRARY")

    if missing:
        print(f"Error: Missing environment variables: {', '.join(missing)}", file=sys.stderr)
        print("\nSet them like this:", file=sys.stderr)
        for var in missing:
            print(f'  export {var}="<value>"', file=sys.stderr)
        sys.exit(1)

    return token, site_url, library


def main():
    parser = argparse.ArgumentParser(description="[MOCK] Transfer Teams recordings to SharePoint")
    parser.add_argument("--search", default=DEFAULT_SEARCH, help=f"Search term (default: '{DEFAULT_SEARCH}')")
    parser.add_argument("--list", action="store_true", help="List matching recordings without transferring")
    parser.add_argument("--file-id", help="Transfer a specific file by ID")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be transferred")
    parser.add_argument("--dest-folder", default="/", help="Destination folder path")
    args = parser.parse_args()

    token, site_url, library = check_env()

    print("[MOCK MODE] Using simulated Graph API responses\n")

    # Search
    if args.file_id:
        matches = [r for r in MOCK_RECORDINGS if r["id"] == args.file_id]
        if not matches:
            print(f"Error: No file found with ID {args.file_id}", file=sys.stderr)
            sys.exit(1)
        file_item = matches[0]
    else:
        print(f"Searching OneDrive for recordings matching: '{args.search}'...")
        matches = [r for r in MOCK_RECORDINGS if args.search.lower() in r["name"].lower()]

        if not matches:
            print(f"\nNo recordings found matching '{args.search}'.")
            sys.exit(1)

        if args.list:
            print(f"\nFound {len(matches)} recording(s):\n")
            for i, rec in enumerate(matches):
                size = fmt_size(rec["size"])
                modified = rec["lastModifiedDateTime"][:19]
                print(f"  {i + 1}. {rec['name']}")
                print(f"     Size: {size} | Modified: {modified} | ID: {rec['id']}")
                print()
            sys.exit(0)

        file_item = matches[0]
        print(f"\nLatest match: {file_item['name']}")
        print(f"  Size: {fmt_size(file_item['size'])}")
        print(f"  Modified: {file_item['lastModifiedDateTime'][:19]}")

        if len(matches) > 1:
            print(f"  ({len(matches) - 1} older recording(s) also match)")

    if args.dry_run:
        print(f"\n[DRY RUN] Would copy to: {site_url} / {library}{args.dest_folder}")
        sys.exit(0)

    # Simulate resolution
    print(f"\nResolving SharePoint destination: {site_url} / {library}...")
    print(f"  Site resolved. Drive ID: mock-drive-abc123...")

    # Simulate copy
    print(f"\nStarting transfer...")
    print(f"Copy started for: {file_item['name']}")
    print(f"  Size: {fmt_size(file_item['size'])}")

    # Simulate progress
    for pct in [25, 50, 75, 100]:
        time.sleep(0.3)
        print(f"  Progress: {pct}% (inProgress)", end="\r")
    print(f"  Copy completed successfully!          ")

    print(f"\n{'='*60}")
    print(f"Transfer complete!")
    print(f"  File: {file_item['name']}")
    print(f"  Size: {fmt_size(file_item['size'])}")
    print(f"  Destination: {site_url} / {library}")
    print(f"{'='*60}")

    result = {
        "status": "success",
        "file_name": file_item["name"],
        "file_size": file_item["size"],
        "destination_site": site_url,
        "destination_library": library,
    }
    print(f"\n{json.dumps(result, indent=2)}")


if __name__ == "__main__":
    main()
