# 🔑 GitHub Token Setup & Integration Guide

## ✅ What's Implemented

### **New Features:**
1. **GitHub Token Storage** - Token saved securely in MongoDB
2. **Auto-Load Settings** - Username, repository, and token auto-fill
3. **Token Help Modal** - Step-by-step guide to get GitHub token
4. **Secure Token Display** - Token masked in UI (shows last 4 characters only)
5. **Automatic Sync** - Uses stored credentials for all GitHub operations

---

## 🎯 How It Works

### **Step 1: Enter GitHub Credentials**
Open Settings (⚙️) and enter:
- **Repository Owner**: Your GitHub username
- **Repository Name**: Your repository name
- **GitHub Token**: Your personal access token (optional but recommended)

### **Step 2: Save & Sync**
Click "🔄 Sync GitHub Data":
1. Settings saved to MongoDB `github_settings` collection
2. Syncs commits, PRs, and issues from your repository
3. Next time you open settings, everything auto-loads!

### **Step 3: View Synced Data**
Dashboard shows:
- ✅ Recent commits with file changes
- ✅ Open/closed issues
- ✅ Incident reports
- ✅ Error logs

---

## 🔐 How to Get GitHub Personal Access Token

### **Quick Steps:**

#### **1. Go to GitHub Token Settings**
Visit: https://github.com/settings/tokens

#### **2. Generate New Token**
- Click **"Generate new token"**
- Select **"Generate new token (classic)"**

#### **3. Configure Token**
```
Note: API Monitoring Token
Expiration: 90 days (recommended)

Required Scopes:
✅ repo - Full control of private repositories
✅ read:org - Read org and team membership (optional)
```

#### **4. Generate & Copy**
- Click **"Generate token"** at bottom
- ⚠️ **COPY IMMEDIATELY** - You won't see it again!
- Token format: `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

#### **5. Paste in Dashboard**
- Open Settings in your dashboard
- Paste token in **"GitHub Personal Access Token"** field
- Click "Sync GitHub Data"
- Token saved securely in MongoDB ✅

---

## 📊 MongoDB Storage

### **Collection: `github_settings`**
```json
{
  "_id": ObjectId("..."),
  "user_id": "default_user",
  "repo_owner": "your-username",
  "repo_name": "your-repo-name",
  "github_token": "ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "updated_at": "2025-10-31T18:30:00Z"
}
```

**Index**: Unique on `user_id`

---

## 🔒 Security Features

### **1. Token Masking**
- Token never displayed in full in UI
- Shows only: `****abcd` (last 4 characters)

### **2. Secure Storage**
- Stored in MongoDB (not in code or logs)
- Not exposed in API responses (masked)

### **3. Optional Token**
- Can use environment variable `GITHUB_TOKEN` instead
- Dashboard token takes priority over env variable

### **4. Update Anytime**
- Enter new token to update
- Leave blank to keep existing token

---

## 🚀 API Endpoints

### **1. Save Settings**
```http
POST /api/github/settings
Content-Type: application/json

{
  "repo_owner": "username",
  "repo_name": "repo-name",
  "github_token": "ghp_xxx..." // optional
}

Response:
{
  "success": true,
  "message": "GitHub settings saved successfully",
  "settings": {
    "repo_owner": "username",
    "repo_name": "repo-name",
    "has_token": true
  }
}
```

### **2. Get Settings**
```http
GET /api/github/settings

Response:
{
  "repo_owner": "username",
  "repo_name": "repo-name",
  "github_token": "****abcd",  // masked
  "has_token": true,
  "updated_at": "2025-10-31T18:30:00Z"
}
```

### **3. Sync GitHub Data**
```http
POST /api/sync/github
Content-Type: application/json

{
  "repo_owner": "username",  // optional if saved
  "repo_name": "repo-name",  // optional if saved
  "since_days": 90
}

Response:
{
  "success": true,
  "commits": {
    "count": 45,
    "synced": 45,
    "skipped": 0
  },
  "pull_requests": {
    "count": 12,
    "synced": 12
  }
}
```

### **4. Sync Issues**
```http
POST /api/sync/issues
Content-Type: application/json

{
  "repo_owner": "username",  // optional if saved
  "repo_name": "repo-name"   // optional if saved
}

Response:
{
  "success": true,
  "count": 8,
  "synced": 8
}
```

---

## 🎨 UI Features

### **Token Help Link**
Click "💡 How to get GitHub token?" to see:
- Step-by-step visual guide
- Direct link to GitHub token settings
- Token format example
- Security best practices

### **Auto-Fill Fields**
When you open settings:
- Repository owner auto-fills
- Repository name auto-fills
- Token status shown (masked)

### **Status Messages**
- ⏳ Loading states
- ✅ Success with details
- ❌ Clear error messages

---

## 📝 Usage Examples

### **First Time Setup**
```javascript
// User opens settings
1. Enter: repo_owner = "john-doe"
2. Enter: repo_name = "my-api-project"
3. Click "How to get GitHub token?" link
4. Follow steps to generate token
5. Paste token: "ghp_abc123..."
6. Click "Sync GitHub Data"
7. ✅ Settings saved + Data synced!
```

### **Subsequent Use**
```javascript
// User opens settings again
1. Fields auto-fill:
   - repo_owner: "john-doe"
   - repo_name: "my-api-project"
   - token: "Token saved: ****123"
2. Just click "Sync GitHub Data"
3. ✅ Uses stored credentials!
```

### **Update Token**
```javascript
// Token expired or needs update
1. Open settings
2. Enter new token in field
3. Click "Sync GitHub Data"
4. ✅ New token saved!
```

---

## 🔄 Data Flow

```
User Input (Dashboard)
    ↓
Save to MongoDB (github_settings)
    ↓
Sync GitHub API
    ↓
Store in MongoDB (git_commits, issues)
    ↓
Display in Dashboard
```

---

## ⚡ Benefits

### **For Developers:**
- ✅ No need to re-enter credentials
- ✅ Token stored securely
- ✅ One-click sync
- ✅ Auto-loads saved settings
- ✅ Built-in help guide

### **For Security:**
- ✅ Token never exposed in UI
- ✅ Stored in database (not code)
- ✅ Masked in all displays
- ✅ Can use env variable as backup

### **For Workflow:**
- ✅ Syncs commits automatically
- ✅ Syncs issues automatically
- ✅ Correlates with API failures
- ✅ Shows recent activity

---

## 🎯 What Gets Synced

### **Commits:**
- Commit ID (SHA)
- Author name and email
- Commit message
- Timestamp
- Files changed
- Lines added/removed

### **Pull Requests:**
- PR number and title
- State (open/closed/merged)
- Author
- Created/merged dates
- Description

### **Issues:**
- Issue number and title
- State (open/closed)
- Labels
- Priority
- Created date
- Description

---

## 🛠️ Troubleshooting

### **"GitHub token not configured"**
**Solution**: Enter token in settings or add to `.env` file:
```env
GITHUB_TOKEN=ghp_your_token_here
```

### **"repo_owner and repo_name required"**
**Solution**: Enter repository details in settings first

### **"Failed to sync"**
**Possible causes:**
- Invalid token (expired or wrong permissions)
- Repository doesn't exist
- Private repo without proper access
- Rate limit exceeded

**Solution**: 
1. Check token has `repo` scope
2. Verify repository name is correct
3. Generate new token if expired

### **Token not saving**
**Solution**: Check MongoDB connection and `github_settings` collection exists

---

## 📚 Token Permissions Explained

### **Required: `repo`**
Allows:
- Read commits
- Read pull requests
- Read issues
- Push files (for dataset export)

### **Optional: `read:org`**
Allows:
- Read organization membership
- Read team membership
- Useful for organization repositories

---

## 🎉 Summary

**What You Can Do Now:**
1. ✅ Store GitHub credentials in MongoDB
2. ✅ Auto-load saved settings
3. ✅ Sync commits, PRs, and issues
4. ✅ View synced data in dashboard
5. ✅ Export monitoring data to GitHub
6. ✅ Get help for token generation
7. ✅ Secure token storage and display

**Everything is ready to use!** 🚀

Just enter your GitHub details once, and the system handles the rest!
