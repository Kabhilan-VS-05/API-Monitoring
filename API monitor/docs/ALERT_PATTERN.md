# 🚨 Alert Pattern: 2 Downtime + 1 Recovery

## ✅ Exactly What You Asked For!

### **Pattern:**
1. **First Alert** - When downtime detected (3+ failures)
2. **Second Alert** - If still down after cooldown (15 min)
3. **STOP** - No more alerts until recovery
4. **Recovery Alert** - When API comes back up (closes all)

---

## 🎯 How It Works

### **Timeline Example:**

```
12:00 PM → API goes down (3 consecutive failures)
         → 🚨 Alert #1 Created (GitHub Issue #45)
         
12:15 PM → Still down (cooldown passed)
         → 🚨 Alert #2 Created (GitHub Issue #46)
         
12:30 PM → Still down
         → ⏸️ NO ALERT (max 2 reached, waiting for recovery)
         
12:45 PM → Still down
         → ⏸️ NO ALERT (waiting for recovery)
         
1:00 PM  → API recovers (3 consecutive successes)
         → ✅ Recovery Alert
         → Closes Issue #45
         → Closes Issue #46
         → Posts recovery comment on both
```

---

## 📊 Visual Flow

```
API Down
    ↓
3 Consecutive Failures
    ↓
🚨 ALERT #1 (GitHub Issue Created)
    ↓
Wait 15 minutes (cooldown)
    ↓
Still Down?
    ├─ YES → 🚨 ALERT #2 (GitHub Issue Created)
    └─ NO → ✅ Recovery (Close Alert #1)
    ↓
Wait 15 minutes (cooldown)
    ↓
Still Down?
    ├─ YES → ⏸️ NO MORE ALERTS (max 2 reached)
    └─ NO → ✅ Recovery (Close Alert #1 & #2)
    ↓
API Recovers (3 consecutive successes)
    ↓
✅ RECOVERY ALERT
    ├─ Close ALL open alerts
    ├─ Add recovery comment
    └─ Calculate total downtime
```

---

## 🎨 GitHub Issues Created

### **Alert #1 (First Downtime)**
```markdown
Title: 🚨 API Downtime Alert: https://api.example.com/endpoint

## 🚨 API Downtime Detected

**Reason:** Downtime Alert #1: 3 consecutive failures

**API URL:** `https://api.example.com/endpoint`  
**Status:** ❌ DOWN  
**Detected At:** 2025-11-01T12:00:00Z  

### 📊 Details
- **Status Code:** 500
- **Error Message:** Connection timeout
- **Response Time:** 5000 ms

Labels: api-downtime, automated, critical
```

### **Alert #2 (Still Down)**
```markdown
Title: 🚨 API Downtime Alert: https://api.example.com/endpoint

## 🚨 API Downtime Detected

**Reason:** Downtime Alert #2: 5 consecutive failures

**API URL:** `https://api.example.com/endpoint`  
**Status:** ❌ DOWN  
**Detected At:** 2025-11-01T12:15:00Z  

### 📊 Details
- **Status Code:** 500
- **Error Message:** Connection timeout
- **Response Time:** 5000 ms

Labels: api-downtime, automated, critical
```

### **Recovery Comment (On Both Issues)**
```markdown
## ✅ API Recovered Successfully!

**Total Alerts Closed:** 2 (Issues: #45, #46)
**Downtime Duration:** 1.0 hours
**Recovered At:** 2025-11-01T13:00:00Z
**Current Status:** ✅ Operational

The API is now responding normally and has been stable for the last 3 checks.

---
*All related downtime alerts have been automatically closed.*
```

---

## 📈 Real-World Scenarios

### **Scenario 1: Quick Recovery (< 15 min)**
```
12:00 → Down (3 failures)
      → 🚨 Alert #1 Created
      
12:10 → Recovers (3 successes)
      → ✅ Recovery Alert
      → Closes Alert #1
      
Result: 1 downtime alert + 1 recovery = 2 total
```

### **Scenario 2: Medium Downtime (15-30 min)**
```
12:00 → Down
      → 🚨 Alert #1 Created
      
12:15 → Still down
      → 🚨 Alert #2 Created
      
12:25 → Recovers
      → ✅ Recovery Alert
      → Closes Alert #1 & #2
      
Result: 2 downtime alerts + 1 recovery = 3 total
```

### **Scenario 3: Long Downtime (> 30 min)**
```
12:00 → Down
      → 🚨 Alert #1 Created
      
12:15 → Still down
      → 🚨 Alert #2 Created
      
12:30 → Still down
      → ⏸️ NO ALERT (max reached)
      
12:45 → Still down
      → ⏸️ NO ALERT (waiting)
      
1:00 → Still down
      → ⏸️ NO ALERT (waiting)
      
2:00 → Recovers
      → ✅ Recovery Alert
      → Closes Alert #1 & #2
      
Result: 2 downtime alerts + 1 recovery = 3 total
(No spam even though down for 2 hours!)
```

---

## 🔧 Configuration

### **Maximum Downtime Alerts**
```python
# In alert_manager.py
self.max_downtime_alerts = 2  # Change to 1, 3, etc.
```

### **Cooldown Between Alerts**
```python
# In alert_manager.py
self.alert_cooldown_minutes = 15  # Change to 10, 20, etc.
```

### **Recovery Threshold**
```python
# In alert_manager.py, method: should_create_recovery_alert()
if consecutive_successes >= 3:  # Change from 3 to your preference
```

---

## 💡 Why This Pattern?

### **Benefits:**

1. **First Alert** - Immediate notification of issue
2. **Second Alert** - Confirms it's not a blip, still down
3. **Stop at 2** - Prevents alert fatigue
4. **One Recovery** - Clean closure, all issues resolved

### **Prevents:**

- ❌ Alert spam (no 10+ alerts for same issue)
- ❌ Notification fatigue (team ignores alerts)
- ❌ Cluttered GitHub (too many open issues)
- ❌ Confusion (which issue is current?)

### **Ensures:**

- ✅ Team knows about issue (2 alerts)
- ✅ Severity communicated (2nd alert = still down)
- ✅ Clean resolution (1 recovery closes all)
- ✅ Accurate metrics (total downtime tracked)

---

## 📊 MongoDB Tracking

### **Alert History During Downtime:**
```json
// Alert #1
{
  "api_id": "507f1f77bcf86cd799439011",
  "alert_type": "downtime",
  "status": "open",
  "github_issue_number": 45,
  "reason": "Downtime Alert #1: 3 consecutive failures",
  "created_at": "2025-11-01T12:00:00Z"
}

// Alert #2
{
  "api_id": "507f1f77bcf86cd799439011",
  "alert_type": "downtime",
  "status": "open",
  "github_issue_number": 46,
  "reason": "Downtime Alert #2: 5 consecutive failures",
  "created_at": "2025-11-01T12:15:00Z"
}
```

### **After Recovery:**
```json
// Both alerts updated
{
  "status": "closed",
  "resolved_at": "2025-11-01T13:00:00Z",
  "downtime_duration": "1.0 hours"
}
```

---

## 🎯 Summary

### **What Happens:**
1. ✅ **Alert #1** - First downtime detected
2. ✅ **Alert #2** - Still down after 15 min
3. ⏸️ **No More** - Max 2 alerts reached
4. ✅ **Recovery** - Closes ALL alerts when API recovers

### **Why It's Smart:**
- **Not too few** - 2 alerts ensure team knows
- **Not too many** - Stops at 2 to prevent spam
- **Clean recovery** - 1 alert closes everything
- **Accurate tracking** - Total downtime calculated

### **Result:**
- 📧 **Less noise** - Max 3 notifications per incident
- 🎯 **Clear status** - Easy to see what's happening
- 📊 **Good metrics** - Downtime duration tracked
- 👥 **Happy team** - No alert fatigue

**Exactly what you asked for: 2 alerts first, then recovery!** 🎉
