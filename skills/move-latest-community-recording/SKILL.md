---
name: move-latest-community-recording
description: Transfer the latest Microsoft Teams meeting recording from OneDrive to SharePoint. Use this skill whenever the user wants to move, transfer, copy, or upload a Teams recording to SharePoint, or wants to archive a Teams recording. Also trigger when the user says things like "move the recording", "upload recording to SharePoint", or "archive the meeting recording".
---

# Move Latest Teams Recording to SharePoint

This skill finds the most recent Microsoft Teams recording matching a configurable search term from the user's OneDrive for Business, and copies it to a specified SharePoint document library using the Microsoft Graph API.

## Why this exists

Teams recordings land in OneDrive by default, but teams often need them archived on a SharePoint site for shared access. Rather than manually downloading and re-uploading, this skill automates the entire flow via the Graph API — find the file, copy it to SharePoint, and confirm success.

## Prerequisites

The skill requires three environment variables to be set before running:

| Variable | Description | Example |
|----------|-------------|---------|
| `MS_GRAPH_TOKEN` | OAuth 2.0 Bearer token for Microsoft Graph API | `eyJ0eXAiOiJKV1Q...` |
| `MS_SHAREPOINT_SITE_URL` | The SharePoint site URL (hostname + site path) | `yourcompany.sharepoint.com:/sites/YourTeam` |
| `MS_SHAREPOINT_LIBRARY` | The document library (drive) name on the target site | `Documents` |

The bearer token needs these Microsoft Graph API permissions:
- `Files.Read` (to read from OneDrive)
- `Files.ReadWrite.All` or `Sites.ReadWrite.All` (to write to SharePoint)

## How to get a bearer token

If the user doesn't have a token ready, walk them through this:

1. Go to [Microsoft Graph Explorer](https://developer.microsoft.com/en-us/graph/graph-explorer)
2. Sign in with your enterprise Microsoft account
3. Under "Access Token", click to copy the token
4. Set it: `export MS_GRAPH_TOKEN="<paste-token-here>"`

Alternatively, if they have an Azure AD app registration:
1. Use the client credentials flow or authorization code flow to obtain a token
2. The token endpoint is: `https://login.microsoftonline.com/{tenant-id}/oauth2/v2.0/token`
3. Scope: `https://graph.microsoft.com/.default`

Note: Graph Explorer tokens expire after about 1 hour. For production use, the user should set up an app registration with refresh token support.

## Step-by-step workflow

### 1. Check environment variables

Before doing anything, verify all three environment variables are set:

```bash
echo "MS_GRAPH_TOKEN: ${MS_GRAPH_TOKEN:+set (${#MS_GRAPH_TOKEN} chars)}"
echo "MS_SHAREPOINT_SITE_URL: ${MS_SHAREPOINT_SITE_URL:-NOT SET}"
echo "MS_SHAREPOINT_LIBRARY: ${MS_SHAREPOINT_LIBRARY:-NOT SET}"
```

If any are missing, tell the user which ones they need to set and how. Do not proceed without all three.

### 2. Determine the search term

Ask the user what recording they want to transfer. The default search term can be any meeting name pattern. Common examples:
- "Weekly Standup"
- "Sprint Review"
- "Team Sync"

If the user doesn't specify, ask them what meeting name to search for.

### 3. Run the transfer script

Execute the bundled Python script:

```bash
python3 SKILL_DIR/scripts/transfer_recording.py --search "<meeting-name-pattern>"
```

Replace `SKILL_DIR` with the actual path to this skill's directory.

The script will:
1. Search OneDrive for files matching the search term in the Recordings folder
2. Pick the most recently modified one
3. Resolve the destination SharePoint site and drive
4. Copy the file to SharePoint using the Graph API's async copy operation
5. Poll until the copy completes
6. Report success with the file name, size, and destination URL

### 3. Report results

If successful, tell the user:
- Which recording was transferred (file name, size, date)
- Where it was copied to (SharePoint site + library)
- A direct link to the file on SharePoint if available

If it failed, show the error and suggest fixes:
- **401 Unauthorized**: Token expired or missing permissions. Guide them to get a new token.
- **404 Not Found**: No recordings matching the search term found, or the SharePoint site/library doesn't exist. Ask them to double-check the config.
- **403 Forbidden**: The token doesn't have write permission to the SharePoint site.

### 4. Custom search term

The script accepts an optional `--search` argument to specify the meeting name pattern:

```bash
python3 SKILL_DIR/scripts/transfer_recording.py --search "Weekly Standup"
```

## Edge cases

- **Multiple matches**: The script always picks the most recently modified file. If the user wants a specific older recording, they can use `--list` to see all matches and then `--file-id <id>` to transfer a specific one.
- **Large files**: Teams recordings can be several GB. The Graph API copy operation is asynchronous — the script polls for completion and reports progress.
- **Token expiry**: Graph Explorer tokens last ~1 hour. If the transfer fails mid-way with a 401, the user needs to refresh their token and retry.
- **Duplicate transfers**: The script does NOT check if the file already exists at the destination. If run twice, it will create a second copy. This is by design — SharePoint handles naming conflicts by appending a number.

## Troubleshooting

If the script fails, check these common issues:

1. **`requests` module not found**: Run `pip3 install requests`
2. **SSL errors**: The enterprise proxy may intercept HTTPS. Try: `export REQUESTS_CA_BUNDLE=/path/to/cert.pem`
3. **Token scope issues**: Make sure the token was issued with the right scopes. Graph Explorer tokens include most common scopes by default, but app registration tokens need explicit scope configuration.
