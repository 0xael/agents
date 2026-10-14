---
name: duplicate-finder
description: Find and safely remove duplicate files in any folder. Use this skill when the user wants to clean up duplicates, find identical files, detect redundant copies, declutter a directory, free up disk space by removing copies, or mentions duplicate/redundant/identical files in any folder (Downloads, Desktop, Documents, etc.). Also use it when the user asks to "clean up" or "organize" a folder and duplicates are likely involved.
---

# Duplicate File Finder & Cleaner

You help users find duplicate files in a specified folder and safely delete them — but only after the user explicitly confirms which files to remove.

## Why this matters

Duplicate files waste disk space and create confusion about which version is the "real" one. But deleting the wrong file can mean losing important work. This skill prioritizes safety: it always shows the user what it found and waits for their go-ahead before touching anything.

## How it works

1. **Scan** the target folder using SHA-256 content hashing (via the bundled script)
2. **Present** duplicate groups to the user in a clear, readable format
3. **Wait** for the user to decide which files to delete
4. **Delete** only the files the user explicitly approves
5. **Summarize** what was removed and how much space was freed

## Step-by-step workflow

### 1. Identify the target folder

Ask the user which folder to scan if they haven't specified one. Common choices:
- `~/Downloads`
- `~/Desktop`
- `~/Documents`

If the user says something vague like "my downloads", resolve it to the appropriate absolute path for their OS.

### 2. Run the duplicate finder script

Execute the bundled Python script to scan the folder:

```bash
python3 SKILL_DIR/scripts/find_duplicates.py "<target-folder>"
```

Replace `SKILL_DIR` with the actual path to this skill's directory. The script outputs a JSON report to stdout with this structure:

```json
{
  "scan_path": "/Users/name/Downloads",
  "total_files_scanned": 142,
  "duplicate_groups": [
    {
      "hash": "abc123...",
      "size_bytes": 1048576,
      "files": [
        "/Users/name/Downloads/report.pdf",
        "/Users/name/Downloads/report (1).pdf"
      ]
    }
  ],
  "total_duplicate_files": 12,
  "total_wasted_bytes": 52428800
}
```

If the script reports errors (permission denied on certain files, etc.), mention them to the user but continue with the files that were successfully scanned.

### 3. Present results clearly

Format the output so the user can understand what was found at a glance. For each group of duplicates:

- Show the file size in human-readable form (KB, MB, GB)
- List all files in the group, numbered
- Indicate which file was created/modified first (the likely "original")

Example presentation:

```
## Duplicate Group 1 (2.4 MB each, 2 copies)
  1. ~/Downloads/report.pdf          (modified: 2024-12-01)
  2. ~/Downloads/report (1).pdf      (modified: 2024-12-15)

## Duplicate Group 2 (850 KB each, 3 copies)
  1. ~/Downloads/photo.jpg           (modified: 2024-11-20)
  2. ~/Downloads/photo copy.jpg      (modified: 2024-11-20)
  3. ~/Downloads/IMG_3021.jpg         (modified: 2024-11-22)
```

End with a summary:
- Total duplicate groups found
- Total space that could be freed
- A clear prompt asking the user what they'd like to do

### 4. Wait for user confirmation

This is the most important step. **Never delete files without explicit user approval.**

**Read the user's intent carefully.** If the user said something like "just show me what's there", "don't delete anything", or "I want to review them first" — respect that. In those cases, end with the summary and a gentle note like "When you're ready to take action, just let me know." Do NOT present a deletion menu or push options on users who explicitly asked for view-only results.

If the user's intent is ambiguous or they seem open to cleaning up, present options like:
- "Delete all duplicates, keeping the oldest version of each"
- "Delete all duplicates, keeping the newest version of each"
- "Let me pick which ones to delete from each group"
- "Don't delete anything — I just wanted to see what's duplicated"

Use the AskUserQuestion tool to collect their choice. If they want to pick individually, walk through each group one at a time.

### 5. Delete approved files and summarize

After getting confirmation:

1. Delete only the files the user approved
2. If a file can't be deleted (permissions, file in use), report the error and continue with the rest
3. Show a final summary:
   - Number of files deleted
   - Total space freed
   - Any files that couldn't be deleted and why

Use `rm` (not `rm -f`) so that errors are visible rather than silently swallowed.

## Edge cases

- **No duplicates found**: Tell the user their folder is clean — no duplicates detected.
- **Empty folder**: Report that the folder is empty or doesn't exist.
- **Very large folders**: The script handles large files efficiently using chunked SHA-256 hashing (reads 8KB at a time). For folders with thousands of files, warn the user the scan might take a moment.
- **Symlinks**: The script skips symbolic links to avoid accidentally following links to other parts of the filesystem.
- **Hidden files**: The script includes hidden files (dotfiles) in the scan. Mention this to the user if hidden file duplicates are found.
- **Nested folders**: The script scans recursively by default. If the user only wants top-level files, they can pass `--no-recurse`.

## Important safety rules

- **Never delete without asking.** Even if the user said "delete all duplicates" in their initial message, still show them what you found and confirm before proceeding.
- **Never use `rm -rf`.** Only delete individual files, never directories.
- **Show full paths.** Always display the complete file path so the user knows exactly what will be affected.
- **Prefer moving to trash when possible.** If the `trash` CLI tool is available (macOS: `brew install trash`), offer to move files to Trash instead of permanently deleting them. This gives the user a safety net.
