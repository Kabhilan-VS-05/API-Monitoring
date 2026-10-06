# 📤 GitHub Dataset Export Feature

## ✅ Implementation Complete

### New Features Added

#### 1. **GitHub Settings Storage in MongoDB**
- Settings are saved when you sync GitHub data
- Settings persist across sessions
- Auto-loads saved repository info when opening settings panel

#### 2. **Export Monitoring Data to GitHub**
- Exports last 30 days of monitoring data as CSV
- Automatically pushes to your GitHub repository
- Updates existing file if it already exists
- Creates file at: `datasets/monitoring_data.csv`

---

## 🎯 How It Works

### **Step 1: Save GitHub Settings**
When you enter repository owner and name and click "Sync GitHub Data":
1. Settings are saved to MongoDB `github_settings` collection
2. Next time you open settings, fields auto-fill with saved values

### **Step 2: Export Dataset**
Click "📤 Export Dataset to GitHub" button:
1. Retrieves your saved GitHub settings from MongoDB
2. Fetches last 30 days of monitoring logs (up to 10,000 records)
3. Converts data to CSV format with columns:
   - timestamp
   - api_id
   - url
   - status_code
   - is_up
   - total_latency_ms
   - dns_latency_ms
   - tcp_latency_ms
   - tls_latency_ms
   - server_processing_latency_ms
   - content_download_latency_ms
   - error_message
   - url_type

4. Pushes CSV file to GitHub repository at `datasets/monitoring_data.csv`
5. Shows success message with link to view file on GitHub

---

## 🔧 API Endpoints Added

### 1. Save GitHub Settings
```
POST /api/github/settings
Body: { "repo_owner": "username", "repo_name": "repo-name" }
```

### 2. Get GitHub Settings
```
GET /api/github/settings
Returns: { "repo_owner": "username", "repo_name": "repo-name", "updated_at": "..." }
```

### 3. Export Dataset to GitHub
```
POST /api/github/export-dataset
Returns: {
  "success": true,
  "message": "Dataset exported to GitHub successfully",
  "file_url": "https://github.com/username/repo/blob/main/datasets/monitoring_data.csv",
  "records_exported": 1234
}
```

---

## 📊 MongoDB Collection

### New Collection: `github_settings`
```json
{
  "user_id": "default_user",
  "repo_owner": "your-username",
  "repo_name": "your-repo",
  "updated_at": "2025-10-31T18:15:00Z"
}
```

**Index**: Unique index on `user_id`

---

## 🎨 UI Changes

### Settings Panel (`monitor.html`)
- Added "📤 Export Dataset to GitHub" button
- Added `exportStatus` div for export feedback

### JavaScript (`monitor.js`)
- Auto-loads saved GitHub settings when panel opens
- Saves settings automatically when syncing
- Export button handler with progress feedback
- Shows clickable link to view exported file on GitHub

---

## 🔐 Requirements

### Environment Variables
Make sure `.env` file has:
```env
GITHUB_TOKEN=your_github_personal_access_token
```

### GitHub Token Permissions
Token needs:
- ✅ `repo` - Full control of private repositories
- ✅ `public_repo` - Access to public repositories

---

## 📝 Usage Example

### First Time Setup:
1. Open Settings panel (⚙️ button)
2. Enter:
   - Repository Owner: `your-username`
   - Repository Name: `your-repo-name`
3. Click "🔄 Sync GitHub Data"
   - Settings saved automatically ✅

### Export Dataset:
1. Open Settings panel
2. Click "📤 Export Dataset to GitHub"
3. Wait for export to complete
4. Click the GitHub link to view your dataset

### Next Time:
- Settings auto-load from MongoDB
- Just click export button directly!

---

## 🎯 Benefits

### For You:
- ✅ No need to re-enter repository info every time
- ✅ One-click dataset export
- ✅ Dataset automatically updates on GitHub
- ✅ Easy to share monitoring data
- ✅ Version controlled dataset history

### For Your Project:
- ✅ Professional dataset management
- ✅ GitHub integration showcases technical skills
- ✅ Easy for others to access your monitoring data
- ✅ Demonstrates full-stack capabilities
- ✅ Portfolio-ready feature

---

## 🚀 What Happens on GitHub

After export, your repository will have:
```
your-repo/
├── datasets/
│   └── monitoring_data.csv  ← Your exported data
├── ... (other files)
```

Each export creates a new commit:
```
Update monitoring dataset - 2025-10-31 18:15:00
```

---

## 🔄 Update Workflow

1. **Monitoring runs** → Data collected in MongoDB
2. **Click export** → CSV generated from MongoDB
3. **Push to GitHub** → Dataset updated automatically
4. **Repeat anytime** → Always get latest data

---

## ⚡ Technical Details

### Data Flow:
```
MongoDB monitoring_logs
    ↓
Python backend (app.py)
    ↓
CSV conversion
    ↓
GitHub API
    ↓
Your repository (datasets/monitoring_data.csv)
```

### File Update Logic:
- First export: Creates new file
- Subsequent exports: Updates existing file (using SHA)
- Preserves commit history on GitHub

---

## 🎉 Summary

**What's New:**
1. ✅ GitHub settings stored in MongoDB
2. ✅ Auto-load saved settings
3. ✅ One-click dataset export to GitHub
4. ✅ CSV format with all monitoring metrics
5. ✅ Automatic file updates on GitHub
6. ✅ Direct link to view exported data

**Ready to Use!**
Just enter your GitHub repo info once, then export anytime! 🚀
