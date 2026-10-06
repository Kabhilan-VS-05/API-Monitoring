# 🔍 Alert Troubleshooting Guide

## ❌ Common Issues

### **Issue 1: Alerts Not Sending Automatically**

#### **Symptoms:**
- API goes down
- No GitHub issue created
- No alert in console logs

#### **Possible Causes:**

**1. GitHub Settings Not Configured**
```
Check Flask console for:
[Alert] ❌ GitHub settings not configured. Please configure in Settings panel.
```

**Solution:**
- Open Insight Dashboard
- Click ⚙️ Settings button
- Fill in:
  - Repository Owner (e.g., `username`)
  - Repository Name (e.g., `my-repo`)
  - GitHub Token (optional, but recommended)
- Click "🔄 Sync GitHub Data"

---

**2. Not Enough Consecutive Failures**
```
Check Flask console for:
[Alert] API xxx status: Down, consecutive failures: 2
[Alert] Not enough consecutive failures (2/3)
```

**Solution:**
- System requires 3 consecutive failures to avoid false positives
- Wait for 3 monitoring cycles (usually 90 seconds)
- Then alert will be created

---

**3. Alert Already Exists**
```
Check Flask console for:
[Alert] API xxx already has open alert #45
```

**Solution:**
- This is normal behavior
- Only one alert per downtime incident
- Close existing GitHub issue first if you want a new one

---

### **Issue 2: Recovery Alert Sent Without Downtime Alert**

#### **Symptoms:**
- API comes back up
- Recovery alert sent
- But no downtime alert was ever sent

#### **Root Cause:**
This should NOT happen with the fixed code. The recovery alert only sends if there's an open downtime alert.

#### **Check:**
```
Look for in Flask console:
[Alert] API xxx has 1 open downtime alert(s)
[Alert] API xxx consecutive successes: 3/3
[Alert] Creating recovery alert for API xxx
```

If you see recovery alert without seeing downtime alert first, there's a bug.

---

## 🔍 Debugging Steps

### **Step 1: Check Flask Console Logs**

When API goes down, you should see:
```
[Alert] API 507f1f77bcf86cd799439011 status: Down, consecutive failures: 3
[Alert] Creating downtime alert for API 507f1f77bcf86cd799439011
[Alert] Attempting to create downtime alert for https://api.example.com
[Alert] Reason: API Down: 3 consecutive failures detected
[Alert] Created downtime alert for https://api.example.com: https://github.com/user/repo/issues/45
[Alert] Downtime/Recovery alert: Success
```

---

### **Step 2: Check MongoDB Alert History**

```javascript
// In MongoDB shell or Compass
db.alert_history.find({}).sort({created_at: -1}).limit(5)
```

Should show:
```json
{
  "_id": ObjectId("..."),
  "api_id": "507f1f77bcf86cd799439011",
  "alert_type": "downtime",
  "status": "open",
  "github_issue_number": 45,
  "github_issue_url": "https://github.com/user/repo/issues/45",
  "reason": "API Down: 3 consecutive failures detected",
  "created_at": "2025-11-01T08:30:00Z"
}
```

---

### **Step 3: Check GitHub Settings in MongoDB**

```javascript
db.github_settings.findOne({user_id: "default_user"})
```

Should show:
```json
{
  "_id": ObjectId("..."),
  "user_id": "default_user",
  "repo_owner": "your-username",
  "repo_name": "your-repo",
  "github_token": "ghp_xxxxxxxxxxxx"
}
```

If this is empty or missing fields, configure in UI.

---

### **Step 4: Check Monitoring Logs**

```javascript
// Check recent logs for API
db.monitoring_logs.find({api_id: "YOUR_API_ID"}).sort({timestamp: -1}).limit(10)
```

Look for:
```json
{
  "api_id": "507f1f77bcf86cd799439011",
  "is_up": false,  // ← Should be false for downtime
  "timestamp": "2025-11-01T08:30:00Z",
  "status_code": 500,
  "error_message": "Connection timeout"
}
```

---

## 🎯 Expected Flow

### **Downtime Detection:**
```
1. Monitoring check runs (every 30 sec)
2. API fails
3. Check 1: ❌ Down
4. Check 2: ❌ Down
5. Check 3: ❌ Down
   ↓
6. 3 consecutive failures detected
   ↓
7. Check if alert already exists → No
   ↓
8. Check GitHub settings → OK
   ↓
9. Create GitHub issue
   ↓
10. Save to alert_history
   ↓
11. Console: "[Alert] Created downtime alert"
```

### **Recovery Detection:**
```
1. Monitoring check runs
2. API succeeds
3. Check 1: ✅ Up
4. Check 2: ✅ Up
5. Check 3: ✅ Up
   ↓
6. 3 consecutive successes detected
   ↓
7. Check if open alert exists → Yes (Issue #45)
   ↓
8. Close GitHub issue #45
   ↓
9. Add recovery comment
   ↓
10. Update alert_history to "closed"
   ↓
11. Console: "[Alert] Closed 1 recovery alerts"
```

---

## 🔧 Manual Testing

### **Test 1: Force Downtime Alert**

1. Add a fake API that will fail:
   ```
   URL: https://this-api-does-not-exist-12345.com/test
   ```

2. Wait 90 seconds (3 checks × 30 sec)

3. Check Flask console for:
   ```
   [Alert] Creating downtime alert for API xxx
   ```

4. Check GitHub for new issue

---

### **Test 2: Force Recovery Alert**

1. After downtime alert is created
2. Delete the fake API or fix it
3. Wait 90 seconds (3 checks)
4. Check Flask console for:
   ```
   [Alert] Creating recovery alert for API xxx
   ```
5. Check GitHub issue is closed

---

## 📊 Console Log Examples

### **Successful Downtime Alert:**
```
[Alert] API 507f1f77bcf86cd799439011 status: Down, consecutive failures: 3
[Alert] Creating downtime alert for API 507f1f77bcf86cd799439011
[Alert] Attempting to create downtime alert for https://api.example.com
[Alert] Reason: API Down: 3 consecutive failures detected
[Alert] Created downtime alert for https://api.example.com: https://github.com/user/repo/issues/45
[Alert] Downtime/Recovery alert: Success
```

### **Failed Alert (No GitHub Settings):**
```
[Alert] API 507f1f77bcf86cd799439011 status: Down, consecutive failures: 3
[Alert] Creating downtime alert for API 507f1f77bcf86cd799439011
[Alert] Attempting to create downtime alert for https://api.example.com
[Alert] Reason: API Down: 3 consecutive failures detected
[Alert] ❌ GitHub settings not configured. Please configure in Settings panel.
```

### **Successful Recovery Alert:**
```
[Alert] API 507f1f77bcf86cd799439011 has 1 open downtime alert(s)
[Alert] API 507f1f77bcf86cd799439011 consecutive successes: 3/3
[Alert] Creating recovery alert for API 507f1f77bcf86cd799439011
[Alert] Closed 1 recovery alerts for https://api.example.com
[Alert] Downtime/Recovery alert: Closed 1 alerts
```

---

## ✅ Checklist

Before expecting automatic alerts, verify:

- [ ] GitHub settings configured in UI
- [ ] Repository owner and name filled in
- [ ] GitHub token provided (or in environment)
- [ ] API has been monitored for at least 90 seconds
- [ ] API has 3+ consecutive failures
- [ ] Flask server is running
- [ ] MongoDB is connected
- [ ] No existing open alert for same API

---

## 🚨 Common Mistakes

### **1. Not Waiting Long Enough**
❌ API down for 30 seconds → No alert
✅ API down for 90+ seconds → Alert sent

### **2. GitHub Settings Empty**
❌ Clicked sync without filling fields
✅ Fill all fields first, then sync

### **3. Expecting Instant Alerts**
❌ API down → Expect immediate alert
✅ API down → Wait 3 checks (90 sec) → Alert

### **4. Token Not Saved**
❌ Entered token but didn't click sync
✅ Enter token → Click "🔄 Sync GitHub Data"

---

## 🎯 Summary

### **For Downtime Alerts:**
1. ✅ Configure GitHub settings
2. ✅ Wait for 3 consecutive failures (90 sec)
3. ✅ Alert automatically created
4. ✅ Check Flask console for confirmation

### **For Recovery Alerts:**
1. ✅ Must have open downtime alert first
2. ✅ Wait for 3 consecutive successes (90 sec)
3. ✅ Recovery alert automatically sent
4. ✅ GitHub issue automatically closed

**Check Flask console logs for detailed debugging!** 🔍
