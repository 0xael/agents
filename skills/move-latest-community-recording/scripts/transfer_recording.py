#!/usr/bin/env python3
"""
Transfer the latest BTP Security Community recording from OneDrive to SharePoint.

Uses Microsoft Graph API with an OAuth 2.0 Bearer token.

Environment variables required:
  MS_GRAPH_TOKEN         - OAuth 2.0 Bearer token
  MS_SHAREPOINT_SITE_URL - SharePoint site (e.g., "company.sharepoint.com:/sites/MySite")
  MS_SHAREPOINT_LIBRARY  - Document library name (e.g., "Documents")

Usage:
  python3 transfer_recording.py                          # Transfer latest BTP Security Community recording
  python3 transfer_recording.py --search "Weekly Call"    # Custom search term
  python3 transfer_recording.py --list                    # List matching recordings without transferring
  python3 transfer_recording.py --file-id <id>            # Transfer a specific file by ID
  python3 transfer_recording.py --dry-run                 # Show what would be transferred without doing it
"""

import argparse
import json
import os
import sys
import time

try:
    import requests
except ImportError:
    print("Error: 'requests' module is required. Install it with: pip3 install requests", file=sys.stderr)
    sys.exit(1)

GRAPH_BASE = "https://graph.microsoft.com/v1.0"
DEFAULT_SEARCH = "BTP Security Community"

# Known OneDrive paths where Teams saves recordings
RECORDING_PATHS = [
    "/me/drive/root:/Recordings:/children",
    "/me/drive/root:/Microsoft Teams Chat Files:/children",
    "/me/drive/search(q='{search}')",
]


def get_headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


def check_env():
    """Verify all required environment variables are set."""
    token = os.environ.get("MS_GRAPH_TOKEN")
    site_url = os.environ.get("MS_SHAREPOINT_SITE_URL")
    library = os.environ.get("MS_SHAREPOINT_LIBRARY")

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


def fmt_size(bytes_val):
    """Format bytes as human-readable size."""
    if bytes_val >= 1024 * 1024 * 1024:
        return f"{bytes_val / 1024 / 1024 / 1024:.1f} GB"
    if bytes_val >= 1024 * 1024:
        return f"{bytes_val / 1024 / 1024:.1f} MB"
    if bytes_val >= 1024:
        return f"{bytes_val / 1024:.1f} KB"
    return f"{bytes_val} bytes"


def search_recordings(token, search_term):
    """Search OneDrive for recordings matching the search term."""
    headers = get_headers(token)
    all_results = []

    # Strategy 1: Search the Recordings folder directly
    for path_template in RECORDING_PATHS[:2]:
        url = f"{GRAPH_BASE}{path_template}"
        try:
            resp = requests.get(url, headers=headers)
            if resp.status_code == 200:
                items = resp.json().get("value", [])
                for item in items:
                    if search_term.lower() in item.get("name", "").lower():
                        all_results.append(item)
        except requests.RequestException:
            continue

    # Strategy 2: Use Graph search API as fallback
    if not all_results:
        search_url = f"{GRAPH_BASE}/me/drive/search(q='{search_term}')"
        try:
            resp = requests.get(search_url, headers=headers)
            if resp.status_code == 200:
                items = resp.json().get("value", [])
                # Filter to video/recording files
                for item in items:
                    name = item.get("name", "").lower()
                    if search_term.lower() in name and (
                        name.endswith(".mp4")
                        or name.endswith(".mkv")
                        or name.endswith(".webm")
                        or "video" in item.get("file", {}).get("mimeType", "")
                    ):
                        all_results.append(item)
        except requests.RequestException:
            pass

    # Deduplicate by ID
    seen = set()
    unique = []
    for item in all_results:
        if item["id"] not in seen:
            seen.add(item["id"])
            unique.append(item)

    # Sort by last modified, newest first
    unique.sort(
        key=lambda x: x.get("lastModifiedDateTime", ""),
        reverse=True,
    )

    return unique


def get_file_by_id(token, file_id):
    """Get a specific file by its OneDrive item ID."""
    headers = get_headers(token)
    url = f"{GRAPH_BASE}/me/drive/items/{file_id}"
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        print(f"Error: Could not find file with ID {file_id}", file=sys.stderr)
        print(f"  Status: {resp.status_code}", file=sys.stderr)
        print(f"  Response: {resp.text[:500]}", file=sys.stderr)
        sys.exit(1)
    return resp.json()


def resolve_sharepoint_drive(token, site_url, library_name):
    """Resolve the SharePoint site and document library to a drive ID."""
    headers = get_headers(token)

    # Get the site
    site_api_url = f"{GRAPH_BASE}/sites/{site_url}"
    resp = requests.get(site_api_url, headers=headers)
    if resp.status_code != 200:
        print(f"Error: Could not resolve SharePoint site: {site_url}", file=sys.stderr)
        print(f"  Status: {resp.status_code}", file=sys.stderr)
        print(f"  Response: {resp.text[:500]}", file=sys.stderr)
        sys.exit(1)

    site_id = resp.json()["id"]

    # Get the drives (document libraries) for this site
    drives_url = f"{GRAPH_BASE}/sites/{site_id}/drives"
    resp = requests.get(drives_url, headers=headers)
    if resp.status_code != 200:
        print(f"Error: Could not list drives for site", file=sys.stderr)
        print(f"  Status: {resp.status_code}", file=sys.stderr)
        sys.exit(1)

    drives = resp.json().get("value", [])
    target_drive = None
    for drive in drives:
        if drive.get("name", "").lower() == library_name.lower():
            target_drive = drive
            break

    if not target_drive:
        available = [d.get("name") for d in drives]
        print(f"Error: Document library '{library_name}' not found.", file=sys.stderr)
        print(f"  Available libraries: {', '.join(available)}", file=sys.stderr)
        sys.exit(1)

    return site_id, target_drive["id"]


def copy_to_sharepoint(token, file_item, dest_drive_id, dest_folder_path="/"):
    """
    Copy a file from OneDrive to a SharePoint document library.
    Uses the Graph API copy endpoint (async operation).
    """
    headers = get_headers(token)
    file_id = file_item["id"]
    file_name = file_item["name"]

    # Build the copy request
    copy_url = f"{GRAPH_BASE}/me/drive/items/{file_id}/copy"

    body = {
        "parentReference": {
            "driveId": dest_drive_id,
            "path": f"/drive/root:{dest_folder_path}" if dest_folder_path != "/" else "/drive/root:",
        },
        "name": file_name,
    }

    resp = requests.post(copy_url, headers=headers, json=body)

    if resp.status_code == 202:
        # Async copy started -- monitor URL is in the Location header
        monitor_url = resp.headers.get("Location")
        print(f"Copy started for: {file_name}")
        print(f"  Size: {fmt_size(file_item.get('size', 0))}")

        if monitor_url:
            return poll_copy_status(monitor_url, file_name)
        else:
            print("  Copy initiated (no monitor URL returned -- check SharePoint manually)")
            return True

    elif resp.status_code == 200 or resp.status_code == 201:
        # Synchronous copy completed (rare for large files)
        print(f"Copy completed: {file_name}")
        return True

    else:
        print(f"Error: Copy failed", file=sys.stderr)
        print(f"  Status: {resp.status_code}", file=sys.stderr)
        print(f"  Response: {resp.text[:500]}", file=sys.stderr)
        return False


def poll_copy_status(monitor_url, file_name, max_wait=600, poll_interval=5):
    """Poll the copy operation status until complete or timeout."""
    elapsed = 0
    while elapsed < max_wait:
        try:
            resp = requests.get(monitor_url)
            if resp.status_code == 200:
                status_data = resp.json()
                status = status_data.get("status")
                pct = status_data.get("percentageComplete", 0)

                if status == "completed":
                    print(f"  Copy completed successfully!")
                    resource_id = status_data.get("resourceId")
                    if resource_id:
                        print(f"  SharePoint item ID: {resource_id}")
                    return True
                elif status == "failed":
                    error = status_data.get("error", {})
                    print(f"  Copy failed: {error.get('message', 'Unknown error')}", file=sys.stderr)
                    return False
                else:
                    print(f"  Progress: {pct}% ({status})", end="\r")

            elif resp.status_code == 303:
                # Redirect means the copy is done
                print(f"  Copy completed successfully!")
                return True

        except requests.RequestException as e:
            print(f"  Warning: Poll request failed: {e}", file=sys.stderr)

        time.sleep(poll_interval)
        elapsed += poll_interval

    print(f"  Timeout: Copy did not complete within {max_wait}s. Check SharePoint manually.", file=sys.stderr)
    return False


def main():
    parser = argparse.ArgumentParser(description="Transfer Teams recordings to SharePoint")
    parser.add_argument("--search", default=DEFAULT_SEARCH, help=f"Search term (default: '{DEFAULT_SEARCH}')")
    parser.add_argument("--list", action="store_true", help="List matching recordings without transferring")
    parser.add_argument("--file-id", help="Transfer a specific file by its OneDrive item ID")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be transferred")
    parser.add_argument("--dest-folder", default="/", help="Destination folder path within the library (default: root)")
    args = parser.parse_args()

    token, site_url, library = check_env()

    # Find the recording
    if args.file_id:
        file_item = get_file_by_id(token, args.file_id)
        print(f"Found file: {file_item['name']} ({fmt_size(file_item.get('size', 0))})")
    else:
        print(f"Searching OneDrive for recordings matching: '{args.search}'...")
        recordings = search_recordings(token, args.search)

        if not recordings:
            print(f"\nNo recordings found matching '{args.search}'.")
            print("Tips:")
            print("  - Check that recordings exist in your OneDrive /Recordings folder")
            print("  - Try a different search term with --search")
            print("  - Make sure your token has Files.Read permission")
            sys.exit(1)

        if args.list:
            print(f"\nFound {len(recordings)} recording(s):\n")
            for i, rec in enumerate(recordings):
                size = fmt_size(rec.get("size", 0))
                modified = rec.get("lastModifiedDateTime", "unknown")[:19]
                print(f"  {i + 1}. {rec['name']}")
                print(f"     Size: {size} | Modified: {modified} | ID: {rec['id']}")
                print()
            sys.exit(0)

        file_item = recordings[0]
        print(f"\nLatest match: {file_item['name']}")
        print(f"  Size: {fmt_size(file_item.get('size', 0))}")
        print(f"  Modified: {file_item.get('lastModifiedDateTime', 'unknown')[:19]}")

        if len(recordings) > 1:
            print(f"  ({len(recordings) - 1} older recording(s) also match)")

    if args.dry_run:
        print(f"\n[DRY RUN] Would copy to: {site_url} / {library}{args.dest_folder}")
        sys.exit(0)

    # Resolve destination
    print(f"\nResolving SharePoint destination: {site_url} / {library}...")
    site_id, drive_id = resolve_sharepoint_drive(token, site_url, library)
    print(f"  Site resolved. Drive ID: {drive_id[:20]}...")

    # Copy the file
    print(f"\nStarting transfer...")
    success = copy_to_sharepoint(token, file_item, drive_id, args.dest_folder)

    if success:
        print(f"\n{'='*60}")
        print(f"Transfer complete!")
        print(f"  File: {file_item['name']}")
        print(f"  Size: {fmt_size(file_item.get('size', 0))}")
        print(f"  Destination: {site_url} / {library}")
        print(f"{'='*60}")
        result = {
            "status": "success",
            "file_name": file_item["name"],
            "file_size": file_item.get("size", 0),
            "destination_site": site_url,
            "destination_library": library,
        }
        print(f"\n{json.dumps(result, indent=2)}")
    else:
        print(f"\nTransfer failed. See errors above.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
