# 🚨 Two Intelligent Alert Systems

## ✅ Exactly What You Asked For!

### **System 1: Immediate Downtime/Recovery Alerts**
- Alert when API goes down
- Alert when API recovers
- Simple and direct

### **System 2: AI Predictive Alerts (Every 15 mins)**
- Trains model every 15 minutes
- Predicts failure probability
- Alerts if high risk detected (>70%)

---

## 🎯 System 1: Immediate Alerts

### **How It Works:**

```
API Monitoring Check
    ↓
Is API Down? (3+ consecutive failures)
    ├─ YES → 🚨 Send GitHub Alert "API Down"
    └─ NO → Continue
    ↓
Was API Down Before?
    ├─ YES → Is it Up Now? (3+ consecutive successes)
    │   ├─ YES → ✅ Send GitHub Alert "API Recovered"
    │   └─ NO → Continue monitoring
    └─ NO → Continue
```

### **Timeline Example:**

```
12:00 PM → API goes down (3 failures)
         → 🚨 GitHub Issue #45: "API Down"
         
12:15 PM → Still down
         → (No new alert, waiting for recovery)
         
12:30 PM → Still down
         → (No new alert, waiting for recovery)
         
1:00 PM  → API recovers (3 successes)
         → ✅ GitHub Issue #45: Comment added + Closed
         → "API Recovered - Downtime: 1.0 hours"
```

### **GitHub Issues Created:**

**When Down:**
```markdown
Title: 🚨 API Downtime Alert: https://api.example.com/endpoint

## 🚨 API Downtime Detected

**Reason:** API Down: 3 consecutive failures detected

**API URL:** `https://api.example.com/endpoint`  
**Status:** ❌ DOWN  
**Detected At:** 2025-11-01T12:00:00Z  

Labels: api-downtime, automated, critical
```

**When Recovered:**
```markdown
## ✅ API Recovered Successfully!

**Total Alerts Closed:** 1 (Issues: #45)
**Downtime Duration:** 1.0 hours
**Recovered At:** 2025-11-01T13:00:00Z
**Current Status:** ✅ Operational

The API is now responding normally and has been stable for the last 3 checks.
```

---

## 🤖 System 2: AI Predictive Alerts

### **How It Works:**

```
Every 15 Minutes (per API):
    ↓
Train AI Model
    ├─ Use last 1000 monitoring logs
    ├─ Analyze patterns
    └─ Learn failure indicators
    ↓
Make Prediction
    ├─ Calculate failure probability
    ├─ Identify risk factors
    └─ Generate recommendations
    ↓
Is Failure Probability > 70%?
    ├─ YES → 🤖 Send GitHub Alert "AI Prediction: High Risk"
    └─ NO → Continue monitoring
    ↓
Is API Now Stable? (10+ consecutive successes)
    ├─ YES → ✅ Close prediction alert
    └─ NO → Keep alert open
```

### **Timeline Example:**

```
12:00 PM → AI trains model
         → Prediction: 45% failure risk
         → (No alert, below threshold)
         
12:15 PM → AI trains model again
         → Prediction: 78% failure risk
         → 🤖 GitHub Issue #50: "AI Prediction: High Risk"
         
12:30 PM → AI trains model
         → Prediction: 82% failure risk
         → (Updates existing alert #50, no new issue)
         
12:45 PM → API still stable (10 successes)
         → ✅ Close Issue #50: "API Stabilized"
```

### **GitHub Issues Created:**

**AI Prediction Alert:**
```markdown
Title: 🤖 AI Prediction: High Failure Risk for https://api.example.com/endpoint

## 🤖 AI Prediction Alert

**API URL:** `https://api.example.com/endpoint`  
**Failure Probability:** 78.5%  
**Prediction Time:** 2025-11-01T12:15:00Z  
**Alert Type:** Predictive (AI-based)

### 📊 AI Analysis

The AI model has detected a **high probability of failure** for this API based on recent patterns and historical data.

**Confidence Level:** 78.5%

### ⚠️ Risk Factors

- Increasing latency trend (200ms → 450ms)
- Error rate spike (2% → 8%)
- Similar pattern to previous failures

### 🔧 Recommended Actions

1. Monitor API closely
2. Review recent code deployments
3. Check server resources
4. Verify database connections

### 💡 What This Means

This is a **predictive alert** - the API may not be down yet, but the AI model predicts a high likelihood of failure.

**Action Required:** Monitor this API closely and consider proactive measures to prevent downtime.

Labels: ai-prediction, automated, warning
```

**When Stabilized:**
```markdown
## ✅ API Stabilized

The API has been stable for the last 10 checks. The predicted failure did not occur.

**Status:** ✅ Stable  
**Resolved At:** 2025-11-01T12:45:00Z

The AI prediction alert is being closed as the API is performing normally.
```

---

## 📊 Comparison

| Feature | System 1: Immediate | System 2: AI Predictive |
|---------|-------------------|----------------------|
| **Trigger** | API actually down | High failure probability |
| **Timing** | Instant (when down) | Every 15 minutes |
| **Purpose** | React to downtime | Prevent downtime |
| **Alert Type** | Critical | Warning |
| **Labels** | `api-downtime`, `critical` | `ai-prediction`, `warning` |
| **Closes When** | API recovers | API stays stable |

---

## 🎯 Real-World Scenarios

### **Scenario 1: Sudden Downtime**
```
System 1:
12:00 → API down
      → 🚨 Alert: "API Down"
12:30 → API recovers
      → ✅ Alert: "API Recovered"

System 2:
12:00 → AI prediction: 35% (no alert)
12:15 → AI prediction: 40% (no alert)
12:30 → AI prediction: 25% (no alert)
```

### **Scenario 2: Gradual Degradation**
```
System 1:
12:00 → API up (no alert)
12:30 → API up (no alert)
1:00 → API down
     → 🚨 Alert: "API Down"

System 2:
12:00 → AI prediction: 55% (no alert)
12:15 → AI prediction: 68% (no alert)
12:30 → AI prediction: 75%
      → 🤖 Alert: "AI Prediction: High Risk"
12:45 → AI prediction: 82% (update existing alert)
1:00 → API actually goes down
     → (System 1 also alerts)
```

### **Scenario 3: False Positive (AI predicts, but doesn't happen)**
```
System 1:
(No alerts - API never went down)

System 2:
12:00 → AI prediction: 72%
      → 🤖 Alert: "AI Prediction: High Risk"
12:15 → AI prediction: 68% (update alert)
12:30 → AI prediction: 45% (update alert)
12:45 → API stable (10 successes)
      → ✅ Close alert: "API Stabilized"
```

---

## 🔧 Configuration

### **System 1 Settings:**
```python
# In alert_manager.py
consecutive_failures = 3  # Failures before alerting
consecutive_successes = 3  # Successes before recovery alert
```

### **System 2 Settings:**
```python
# In ai_alert_manager.py
self.training_interval_minutes = 15  # Train every 15 mins
self.prediction_threshold = 0.7  # 70% probability triggers alert
minimum_data_points = 50  # Minimum logs needed for training
```

---

## 📈 Benefits

### **System 1: Immediate Alerts**
- ✅ **Instant notification** when downtime occurs
- ✅ **Clear recovery** notification
- ✅ **Simple and reliable**
- ✅ **No false positives** (only alerts when actually down)

### **System 2: AI Predictive**
- ✅ **Proactive** - Catch issues before they happen
- ✅ **Smart** - Uses machine learning
- ✅ **Actionable** - Provides recommendations
- ✅ **Self-correcting** - Closes if prediction wrong

---

## 🎨 Visual Flow

```
┌─────────────────────────────────────────┐
│         Monitoring Check                │
└─────────────────┬───────────────────────┘
                  │
        ┌─────────┴─────────┐
        │                   │
        ▼                   ▼
┌───────────────┐   ┌──────────────────┐
│   System 1    │   │    System 2      │
│   Immediate   │   │  AI Predictive   │
└───────┬───────┘   └────────┬─────────┘
        │                    │
        │                    │
   Is Down?            Train Model
        │              (Every 15 min)
        ▼                    │
    YES → 🚨                 ▼
    Alert "Down"      Predict Failure
        │                    │
        ▼                    ▼
   Recovers?          High Risk? (>70%)
        │                    │
        ▼                    ▼
    YES → ✅            YES → 🤖
    Alert "Up"         Alert "Prediction"
```

---

## 💡 Why Two Systems?

### **System 1 (Immediate):**
- **Reactive** - Tells you when problem exists
- **Reliable** - No false positives
- **Critical** - Requires immediate action

### **System 2 (AI Predictive):**
- **Proactive** - Tells you problem might occur
- **Preventive** - Time to fix before downtime
- **Warning** - Suggests preventive action

### **Together:**
- **Complete coverage** - React + Prevent
- **No missed issues** - Catch everything
- **Smart alerting** - Right alert at right time
- **Reduced downtime** - Fix before it breaks

---

## 📊 MongoDB Collections

### **alert_history (Both Systems)**

**System 1 Alert:**
```json
{
  "api_id": "507f1f77bcf86cd799439011",
  "alert_type": "downtime",
  "status": "open",
  "github_issue_number": 45,
  "reason": "API Down: 3 consecutive failures detected",
  "created_at": "2025-11-01T12:00:00Z"
}
```

**System 2 Alert:**
```json
{
  "api_id": "507f1f77bcf86cd799439011",
  "alert_type": "ai_prediction",
  "status": "open",
  "github_issue_number": 50,
  "failure_probability": 0.785,
  "prediction_data": {...},
  "created_at": "2025-11-01T12:15:00Z"
}
```

---

## 🚀 Summary

### **What You Get:**

**System 1:**
1. ✅ Alert when API goes down
2. ✅ Alert when API recovers
3. ✅ Simple, direct, reliable

**System 2:**
1. 🤖 AI trains every 15 minutes
2. 🤖 Predicts failure probability
3. 🤖 Alerts if >70% risk
4. 🤖 Closes if API stays stable

### **Result:**
- **Immediate alerts** for actual downtime
- **Predictive alerts** for potential issues
- **Complete coverage** - nothing missed
- **Smart automation** - no manual work

**Both systems work together automatically!** 🎯

Just restart Flask and both systems activate!
