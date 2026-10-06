# 🚨 GitHub Downtime Alerts Feature

## ✅ What's Implemented

### **Automatic GitHub Issue Creation for API Downtime**

When an API goes down, you can now automatically create a GitHub issue with:
- ✅ Detailed downtime information
- ✅ Error messages and status codes
- ✅ Latency breakdown
- ✅ Recommended actions
- ✅ Automatic labels and formatting

---

## 🎯 How It Works

### **1. Detect Downtime**
- System monitors APIs continuously
- When API status = "Down", a red button appears

### **2. Create GitHub Alert**
- Click "🚨 Create GitHub Alert" button on down API
- Confirm creation
- GitHub issue automatically created in your repository

### **3. GitHub Issue Contains:**
```markdown
## 🚨 API Downtime Detected

**API URL:** `https://api.example.com/endpoint`  
**Status:** ❌ DOWN  
**Detected At:** 2025-10-31T18:30:00Z  

### 📊 Details
- **Status Code:** 500
- **Error Message:** Connection timeout
- **Response Time:** 5000 ms
- **URL Type:** REST API

### 🔍 Latency Breakdown
- **DNS Latency:** 50 ms
- **TCP Latency:** 100 ms
- **TLS Latency:** 150 ms
- **Server Processing:** 4700 ms

### 📈 Recent History
API has been down since 2025-10-31T18:30:00Z

### 🔧 Recommended Actions
1. Check server logs for errors
2. Verify API endpoint configuration
3. Test network connectivity
4. Review recent code deployments
5. Check database connections

---
*This issue was automatically created by API Monitoring System*  
*Incident ID: INC-1730389800*
```

### **4. Issue Labels**
Automatically tagged with:
- `api-downtime` - Identifies as downtime alert
- `automated` - Created by system
- `critical` - High priority

---

## 🎨 UI Features

### **Downtime Alert Button**
- **Appears**: Only when API status = "Down"
- **Color**: Red background (#DA3633)
- **Icon**: 🚨 Alert emoji
- **Location**: Below AI Insights button on monitor card

### **Confirmation Dialog**
- Asks: "Create a GitHub issue for this API downtime?"
- Prevents accidental issue creation

### **Success Message**
```
✅ GitHub Issue Created!

Issue #123

View at: https://github.com/username/repo/issues/123
```

---

## 🔧 API Endpoint

### **Create Downtime Alert**
```http
POST /api/github/create-downtime-alert
Content-Type: application/json

{
  "api_id": "507f1f77bcf86cd799439011"
}

Response:
{
  "success": true,
  "issue_number": 123,
  "issue_url": "https://github.com/username/repo/issues/123",
  "message": "GitHub issue #123 created successfully"
}
```

---

## 📋 Requirements

### **1. GitHub Settings Configured**
- Repository owner saved
- Repository name saved
- GitHub token saved (with `repo` scope)

### **2. API Must Be Down**
- Latest monitoring log shows `is_up: false`
- System detected actual downtime

### **3. GitHub Token Permissions**
Required scopes:
- ✅ `repo` - Create issues in repository
- ✅ `public_repo` - For public repositories

---

## 🚀 Usage Example

### **Scenario: Payment API Goes Down**

1. **Dashboard shows:**
   ```
   Payment API
   Status: ❌ Down
   Uptime: 95.5%
   ```

2. **Click "🚨 Create GitHub Alert"**

3. **Confirm creation**

4. **GitHub Issue Created:**
   - Title: "🚨 API Downtime Alert: https://api.payment.com/v1/charge"
   - Body: Full details with metrics
   - Labels: api-downtime, automated, critical
   - Assignees: (optional, can be configured)

5. **Team Gets Notified:**
   - GitHub sends notifications
   - Team members see issue
   - Can comment and collaborate
   - Track resolution progress

6. **When Fixed:**
   - API comes back up
   - Can manually close issue or use auto-close feature

---

## 🔄 Workflow Integration

### **Complete Downtime Response Flow:**

```
API Goes Down
    ↓
Dashboard Shows Red Status
    ↓
Click "Create GitHub Alert"
    ↓
GitHub Issue Created
    ↓
Team Notified via GitHub
    ↓
Team Investigates & Fixes
    ↓
API Restored
    ↓
Issue Closed with Resolution
```

---

## 🎯 Benefits

### **For Teams:**
- ✅ **Centralized Tracking** - All downtime incidents in GitHub
- ✅ **Team Collaboration** - Comment, assign, label
- ✅ **Audit Trail** - Complete history of incidents
- ✅ **Integration** - Works with GitHub Projects, Actions

### **For Developers:**
- ✅ **Quick Alerts** - One-click issue creation
- ✅ **Detailed Context** - All metrics included
- ✅ **Actionable** - Recommended steps provided
- ✅ **Automated** - No manual issue writing

### **For Management:**
- ✅ **Visibility** - See all downtime incidents
- ✅ **Metrics** - Track MTTR (Mean Time To Resolve)
- ✅ **Accountability** - Assign to team members
- ✅ **Reporting** - GitHub insights and analytics

---

## 📊 Issue Data Included

### **Automatically Captured:**
1. **API URL** - Exact endpoint that failed
2. **Timestamp** - When downtime detected
3. **Status Code** - HTTP response code
4. **Error Message** - Detailed error description
5. **Latency Metrics** - DNS, TCP, TLS, Server times
6. **URL Type** - REST, GraphQL, SOAP, etc.
7. **Incident ID** - Unique identifier
8. **History** - Recent downtime duration

---

## 🔐 Security & Privacy

### **Token Security:**
- Token stored securely in MongoDB
- Never exposed in issue content
- Used only for GitHub API calls

### **Issue Visibility:**
- Public repos: Issues visible to all
- Private repos: Only team members see
- Configure repository visibility as needed

### **Data Included:**
- Only monitoring metrics
- No sensitive API keys or tokens
- No user data or PII

---

## 🛠️ Advanced Features

### **Future Enhancements (Can Be Added):**

1. **Auto-Close Issues**
   - When API comes back up
   - Add resolution comment
   - Update with uptime restored

2. **Assignees**
   - Auto-assign based on API category
   - Rotate on-call engineers
   - Team-based assignment

3. **Custom Labels**
   - Add category labels
   - Severity levels
   - Service tags

4. **Slack Integration**
   - Post to Slack when issue created
   - Link to GitHub issue
   - Real-time notifications

5. **Incident Metrics**
   - Track MTTR
   - Downtime duration
   - Frequency analysis

---

## 📝 Code Implementation

### **Backend (Python):**
```python
# issue_integration.py
def create_downtime_alert(self, repo_owner, repo_name, api_url, downtime_data):
    """Create GitHub issue for API downtime"""
    # Build issue with markdown formatting
    # POST to GitHub API
    # Store in MongoDB
    # Return issue URL
```

### **Frontend (JavaScript):**
```javascript
// monitor.js
async function createGitHubAlert(apiId) {
    // Confirm with user
    // POST to /api/github/create-downtime-alert
    // Show success message with issue link
}
```

### **API Endpoint:**
```python
# app.py
@app.route("/api/github/create-downtime-alert", methods=["POST"])
def create_downtime_alert():
    # Get API details
    # Get latest downtime log
    # Create GitHub issue
    # Return result
```

---

## 🎉 Summary

**What You Can Do:**
1. ✅ Monitor APIs for downtime
2. ✅ Click button to create GitHub issue
3. ✅ Issue includes all relevant metrics
4. ✅ Team gets notified automatically
5. ✅ Track and resolve in GitHub
6. ✅ Complete audit trail

**GitHub Issue Includes:**
- 🚨 Alert status
- 📊 Detailed metrics
- 🔍 Latency breakdown
- 📈 Recent history
- 🔧 Recommended actions
- 🏷️ Automatic labels

**Perfect For:**
- Team collaboration
- Incident tracking
- Downtime documentation
- Performance monitoring
- SLA compliance

**Everything is ready to use!** 🚀

Just configure GitHub settings and click the alert button when downtime occurs!
