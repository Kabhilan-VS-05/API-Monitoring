# GitHub Integration Guide

## Overview
The API Monitoring Dashboard includes comprehensive GitHub integration to sync commits, pull requests, and issues from your repositories.

## Features
- ✅ Sync commits from GitHub repositories
- ✅ Sync pull requests (open, closed, merged)
- ✅ Sync issues (excluding PRs)
- ✅ Automatic sync when panel opens (if repo details are filled)
- ✅ Manual sync via button click
- ✅ Support for GitHub Personal Access Token (via UI or environment variable)
- ✅ Real-time sync status with Lucide icons
- ✅ Data stored in MongoDB for persistence

## Setup Instructions

### 1. Create GitHub Personal Access Token

1. Go to GitHub Settings: https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. Give it a descriptive name (e.g., "API Monitoring Dashboard")
4. Select the following scopes:
   - ✅ `repo` (Full control of private repositories)
   - ✅ `read:org` (Read org and team membership)
5. Click "Generate token"
6. **IMPORTANT**: Copy the token immediately (you won't see it again!)

### 2. Configure the Token

You have two options:

#### Option A: Via Environment Variable (Recommended for production)
1. Copy `.env.example` to `.env`:
   ```bash
   copy .env.example .env
   ```
2. Edit `.env` and add your token:
   ```
   GITHUB_TOKEN=ghp_your_actual_token_here
   ```
3. Restart the application

#### Option B: Via UI (Recommended for testing)
1. Open the Advanced Dashboard
2. Click the Settings icon (⚙️)
3. Enter your GitHub token in the "GitHub Personal Access Token" field
4. The token will be sent with each sync request

### 3. Configure Repository Details

In the Developer Data Integration panel:
1. **Repository Owner**: Your GitHub username or organization (e.g., `Kabhilan-VS-05`)
2. **Repository Name**: The repository name (e.g., `API-Monitoring`)
3. **Days to fetch**: Number of days of history to sync (default: 90)

## Usage

### Automatic Sync
When you open the Developer Data Integration panel (Settings button), the system will automatically sync GitHub data if:
- Repository owner and name are filled in
- Either a token is provided in the UI or configured in environment variables

### Manual Sync
Click the "Sync GitHub Data" button to manually trigger a sync at any time.

### Sync Status Messages
- 🔄 **Loading**: "Syncing GitHub data..."
- ✅ **Success**: "Synced X commits, Y PRs, and Z issues"
- ❌ **Error**: Shows the specific error message

## API Endpoints

### Sync GitHub Commits & PRs
```
POST /api/sync/github
Content-Type: application/json

{
  "repo_owner": "Kabhilan-VS-05",
  "repo_name": "API-Monitoring",
  "since_days": 90,
  "token": "ghp_optional_token_here"  // Optional if set in env
}
```

**Response:**
```json
{
  "success": true,
  "commits": {
    "success": true,
    "count": 45
  },
  "pull_requests": {
    "success": true,
    "count": 12
  }
}
```

### Sync GitHub Issues
```
POST /api/sync/issues
Content-Type: application/json

{
  "repo_owner": "Kabhilan-VS-05",
  "repo_name": "API-Monitoring",
  "token": "ghp_optional_token_here"  // Optional if set in env
}
```

**Response:**
```json
{
  "success": true,
  "count": 8
}
```

### Get Recent Commits
```
GET /api/commits?hours=168
```

**Response:**
```json
[
  {
    "commit_id": "abc123...",
    "repository": "Kabhilan-VS-05/API-Monitoring",
    "author": "John Doe",
    "message": "Fix bug in API monitoring",
    "timestamp": "2024-10-31T12:00:00Z",
    "files_changed": ["app.py", "monitor.js"],
    "additions": 45,
    "deletions": 12
  }
]
```

### Get Issues
```
GET /api/issues?state=open
```

**Response:**
```json
[
  {
    "issue_id": "github_owner_repo_123",
    "number": 123,
    "title": "Bug in sync function",
    "state": "open",
    "labels": ["bug", "priority: high"],
    "created_at": "2024-10-30T10:00:00Z"
  }
]
```

## Data Storage

All synced data is stored in MongoDB:

### Collections:
- **git_commits**: Stores commit data with files changed, additions, deletions
- **pull_requests**: Stores PR data with state, merge status
- **issues**: Stores issue data with labels, priority, state
- **incident_reports**: Links incidents to commits and issues

### Indexes:
- `commit_id` (unique)
- `pr_id` (unique)
- `issue_id` (unique)
- `timestamp` (for time-based queries)

## Troubleshooting

### Error: "GitHub token not provided or configured"
**Solution**: Provide a token either via the UI or set `GITHUB_TOKEN` in your `.env` file.

### Error: "401 Unauthorized"
**Solution**: Your token is invalid or expired. Generate a new token with the correct scopes.

### Error: "403 Forbidden" or "Rate limit exceeded"
**Solution**: 
- GitHub API has rate limits (5000 requests/hour for authenticated users)
- Wait for the rate limit to reset
- Use a token with higher rate limits

### Error: "404 Not Found"
**Solution**: 
- Check that the repository owner and name are correct
- Ensure your token has access to the repository (especially for private repos)

### No data showing after sync
**Solution**:
- Check the browser console for errors
- Verify MongoDB is running and connected
- Check the server logs for sync errors

## Best Practices

1. **Token Security**:
   - Never commit tokens to version control
   - Use environment variables for production
   - Rotate tokens regularly

2. **Sync Frequency**:
   - Don't sync too frequently (respect rate limits)
   - Use reasonable `since_days` values (7-90 days)
   - Consider caching results

3. **Data Management**:
   - Regularly clean old data from MongoDB
   - Monitor database size
   - Use indexes for better query performance

## Files Involved

### Backend:
- `github_integration.py` - GitHub API client for commits and PRs
- `issue_integration.py` - GitHub API client for issues
- `app.py` - API endpoints for sync operations

### Frontend:
- `static_advanced/monitor.js` - Sync logic and UI updates
- `static_advanced/monitor.html` - UI for GitHub integration panel

### Configuration:
- `.env` - Environment variables (create from `.env.example`)
- `.env.example` - Template for environment configuration

## Support

For issues or questions:
1. Check the browser console for JavaScript errors
2. Check the server logs for Python errors
3. Verify MongoDB connection and data
4. Review GitHub API documentation: https://docs.github.com/en/rest

## Future Enhancements

Potential improvements:
- [ ] Support for multiple repositories
- [ ] Webhook integration for real-time updates
- [ ] GitHub Actions integration
- [ ] Branch-specific syncing
- [ ] Commit diff visualization
- [ ] PR review comments sync
- [ ] Issue comment sync
