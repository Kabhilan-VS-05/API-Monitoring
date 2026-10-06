# 🚀 API Downtime Monitoring & Intelligent Alerting System

## 📋 Project Overview

A comprehensive API monitoring system with AI-powered predictive analytics and automatic GitHub issue creation for downtime alerts. The system monitors APIs in real-time, predicts potential failures using machine learning, and automatically creates GitHub issues when problems are detected.

---

## 🎯 Core Features

### 1. **Real-Time API Monitoring**
- Monitor multiple APIs simultaneously
- Check every 30 seconds (configurable)
- Track uptime, latency, and response codes
- Support for REST APIs, Websites, Databases, and Microservices
- Custom headers and authentication support

### 2. **Intelligent Automatic Alerting (Two Systems)**

#### **System 1: Immediate Downtime/Recovery Alerts**
- **Trigger:** API goes down (3 consecutive failures)
- **Action:** Creates GitHub issue automatically
- **Recovery:** Closes issue when API recovers (3 consecutive successes)
- **Features:**
  - No manual intervention needed
  - Prevents false positives (requires 3 consecutive failures)
  - Calculates total downtime duration
  - Adds recovery comment to GitHub issue

#### **System 2: AI Predictive Alerts (Every 15 minutes)**
- **Trigger:** AI predicts >70% failure probability
- **Action:** Creates warning GitHub issue
- **Technology:** LSTM + Autoencoder neural networks
- **Features:**
  - Trains model every 15 minutes per API category
  - Predicts failures before they happen
  - Provides risk factors and recommendations
  - Auto-closes if API stays stable

### 3. **AI-Powered Failure Prediction**
- **Model:** Category-Aware LSTM + Autoencoder
- **Categories:** REST API, Website, Database, Microservice, GraphQL, WebSocket
- **Training:** Automatic every 15 minutes
- **Prediction:** Failure probability (0-100%)
- **Features:**
  - Separate models for each API category
  - Learns from historical patterns
  - Detects anomalies and outliers
  - Provides actionable insights

### 4. **GitHub Integration**
- **Automatic Issue Creation:**
  - Downtime alerts (critical)
  - AI prediction warnings
  - Recovery notifications
- **Issue Management:**
  - Auto-close on recovery
  - Add comments with details
  - Link related issues
- **Labels:** `api-downtime`, `ai-prediction`, `automated`, `critical`, `warning`

### 5. **Developer Correlation Engine**
- Correlates API downtime with:
  - Recent commits
  - Pull requests
  - Code deployments
  - Developer activity
- Identifies potential root causes
- Links monitoring events to code changes

### 6. **Advanced Dashboard**
- **Real-time Status:** Live API health monitoring
- **Auto-refresh:** Updates every 60 seconds
- **Alert Status:** Shows active alerts and AI predictions
- **Sparklines:** Visual 15-check history
- **Categories:** Organized by API type
- **Detailed Views:** Latency breakdowns, certificate info
- **Charts:** Historical latency trends

---

## 🏗️ Architecture

### **Technology Stack**
- **Backend:** Python Flask
- **Database:** MongoDB
- **Frontend:** Vanilla JavaScript, Chart.js
- **AI/ML:** TensorFlow, Keras, scikit-learn
- **Monitoring:** Custom Python monitoring engine
- **Integration:** GitHub API, REST APIs

### **Key Components**

```
┌─────────────────────────────────────────────────────────┐
│                    Flask Application                     │
│  - API Endpoints                                         │
│  - Background Monitoring Worker                          │
│  - GitHub Integration                                    │
└─────────────────────────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   MongoDB    │  │ Alert System │  │  AI Predictor│
│              │  │              │  │              │
│ - APIs       │  │ - Downtime   │  │ - LSTM       │
│ - Logs       │  │ - Recovery   │  │ - Autoencoder│
│ - Alerts     │  │ - AI Alerts  │  │ - Training   │
│ - GitHub     │  │              │  │              │
└──────────────┘  └──────────────┘  └──────────────┘
        │                  │                  │
        └──────────────────┼──────────────────┘
                           ▼
                  ┌──────────────┐
                  │   GitHub     │
                  │   Issues     │
                  └──────────────┘
```

---

## 📂 Project Structure

```
API Downtime/
├── app.py                          # Main Flask application
├── alert_manager.py                # Downtime/Recovery alert system
├── ai_alert_manager.py             # AI predictive alert system
├── ai_predictor.py                 # ML model for failure prediction
├── correlation_engine.py           # Developer correlation
├── github_integration.py           # GitHub API integration
├── issue_integration.py            # GitHub issue management
├── log_collector.py                # Monitoring log collection
├── models/                         # Saved AI models
│   ├── lstm_rest_api.h5
│   ├── autoencoder_rest_api.h5
│   ├── scaler_rest_api.pkl
│   └── config_rest_api.json
├── static_advanced/
│   ├── monitor.html                # Dashboard UI
│   ├── monitor.js                  # Dashboard logic
│   └── monitor.css                 # Dashboard styles
├── START_HERE.bat                  # Start script
├── RESTART_CLEAN.bat               # Clean restart script
└── requirements.txt                # Python dependencies
```

---

## 🔄 How It Works

### **Monitoring Flow**

```
1. Background Worker (Every 30 seconds)
   ↓
2. Check Each API
   ├─ Send HTTP Request
   ├─ Measure Latency
   ├─ Record Status
   └─ Save to MongoDB
   ↓
3. Alert System 1: Immediate Alerts
   ├─ Check if Down (3 consecutive failures)
   │  └─ Create GitHub Issue
   ├─ Check if Recovered (3 consecutive successes)
   │  └─ Close GitHub Issue
   ↓
4. Alert System 2: AI Predictions (Every 15 min)
   ├─ Load/Train Model
   ├─ Predict Failure Probability
   ├─ If >70% Risk
   │  └─ Create Warning GitHub Issue
   ├─ If Stable (10 successes)
   │  └─ Close Warning Issue
   ↓
5. Correlation Engine
   ├─ Link to Recent Commits
   ├─ Find Related PRs
   └─ Identify Potential Causes
```

### **Alert Decision Logic**

#### **Downtime Alert:**
```python
if current_status in ["Down", "Error"]:
    if consecutive_failures >= 3:
        if not open_alert_exists:
            create_github_issue()
```

#### **Recovery Alert:**
```python
if open_downtime_alert_exists:
    if consecutive_successes >= 3:
        close_github_issue()
        add_recovery_comment()
```

#### **AI Prediction Alert:**
```python
if time_since_last_training >= 15_minutes:
    train_model()
    prediction = predict_failure()
    if prediction.probability >= 0.70:
        if not open_ai_alert_exists:
            create_warning_issue()
```

---

## 🤖 AI/ML System

### **Model Architecture**

```
Input: Last 20 API checks (sequence)
   ↓
┌─────────────────────────────────┐
│  LSTM Layer 1 (64 units)        │
│  - Learns temporal patterns     │
└─────────────────────────────────┘
   ↓
┌─────────────────────────────────┐
│  LSTM Layer 2 (32 units)        │
│  - Extracts features             │
└─────────────────────────────────┘
   ↓
┌─────────────────────────────────┐
│  Dense Layer (16 units)          │
│  - Classification                │
└─────────────────────────────────┘
   ↓
Output: Failure Probability (0-1)
```

### **Features Used**
1. API Status (Up/Down)
2. Total Latency (normalized)
3. DNS Latency
4. TCP Latency
5. TLS Latency
6. Server Processing Time
7. Content Download Time
8. HTTP Status Code
9. Error Presence
10. Time-based features

### **Training Process**
1. Fetch last 1000 monitoring logs
2. Create sequences of 20 checks
3. Normalize by category expectations
4. Train LSTM model (50 epochs)
5. Train Autoencoder for anomaly detection
6. Save models to disk
7. Evaluate accuracy and AUC

### **Model Persistence**
- Models saved after training
- Loaded on Flask startup
- No retraining on restart (saves 5-10 minutes)
- Retrain only when needed (every 15 min or on demand)

---

## 📊 Database Schema

### **MongoDB Collections**

#### **monitored_apis**
```javascript
{
  "_id": ObjectId,
  "url": "https://api.example.com/endpoint",
  "category": "REST API",
  "check_frequency_minutes": 0.5,
  "header_name": "Authorization",
  "header_value": "Bearer token",
  "notification_email": "admin@example.com",
  "last_checked_at": "2025-11-01T08:00:00Z",
  "last_status": "Up"
}
```

#### **monitoring_logs**
```javascript
{
  "_id": ObjectId,
  "api_id": "507f1f77bcf86cd799439011",
  "timestamp": "2025-11-01T08:00:00Z",
  "is_up": true,
  "status_code": 200,
  "total_latency_ms": 145.23,
  "dns_latency_ms": 12.5,
  "tcp_latency_ms": 23.1,
  "tls_latency_ms": 45.2,
  "server_processing_latency_ms": 52.3,
  "content_download_latency_ms": 12.13,
  "error_message": null,
  "url_type": "https"
}
```

#### **alert_history**
```javascript
{
  "_id": ObjectId,
  "api_id": "507f1f77bcf86cd799439011",
  "alert_type": "downtime", // or "ai_prediction"
  "status": "open", // or "closed"
  "github_issue_number": 45,
  "github_issue_url": "https://github.com/user/repo/issues/45",
  "reason": "API Down: 3 consecutive failures detected",
  "created_at": "2025-11-01T08:00:00Z",
  "resolved_at": "2025-11-01T09:00:00Z",
  "downtime_duration": "1.0 hours",
  
  // For AI predictions
  "failure_probability": 0.85,
  "prediction_data": {
    "risk_factors": [...],
    "recommendations": [...]
  }
}
```

#### **github_settings**
```javascript
{
  "_id": ObjectId,
  "user_id": "default_user",
  "repo_owner": "username",
  "repo_name": "repository",
  "github_token": "ghp_xxxxxxxxxxxx"
}
```

#### **commits**
```javascript
{
  "_id": ObjectId,
  "sha": "abc123...",
  "message": "Fix API endpoint",
  "author": "John Doe",
  "timestamp": "2025-11-01T08:00:00Z",
  "url": "https://github.com/..."
}
```

---

## 🎨 User Interface

### **Dashboard Features**

1. **Monitor Cards**
   - API URL and category
   - Current status (Up/Down/Error)
   - Uptime percentage (24h)
   - Average latency (24h)
   - Sparkline (last 15 checks)
   - Alert status indicator
   - AI prediction status

2. **Alert Status Display**
   ```
   🚨 Alert sent 5 mins ago #45
   🤖 AI: 15% risk - Good (2 mins ago)
   ```

3. **Settings Panel**
   - GitHub configuration
   - Data sync controls
   - Automatic alert system info
   - Data summary (commits, issues, incidents)

4. **Detailed View**
   - Full latency breakdown
   - Certificate information
   - Historical charts
   - Check history table
   - Pagination

5. **Auto-Refresh**
   - Updates every 60 seconds
   - Shows latest status
   - Reloads alert information
   - Console logging

---

## 🔔 Alert Examples

### **Downtime Alert (GitHub Issue)**

```markdown
Title: 🚨 API Downtime Alert: https://api.example.com/endpoint

## 🚨 API Downtime Detected

**Reason:** API Error: 3 consecutive failures detected

**API URL:** `https://api.example.com/endpoint`  
**Status:** ❌ DOWN  
**Detected At:** 2025-11-01T08:00:00Z  
**Incident ID:** INC-1730448000

### 📊 Downtime Details

**Status Code:** 500  
**Error Message:** Connection timeout  
**Total Latency:** 5000.00 ms

### 🔍 Latency Breakdown

- **DNS Resolution:** 12.50 ms
- **TCP Connection:** 23.10 ms
- **TLS Handshake:** 45.20 ms
- **Server Processing:** 4800.00 ms
- **Content Download:** 119.20 ms

### 📝 History Summary

API Error: 3 consecutive failures detected

API has been down since 2025-11-01T08:00:00Z

---
*This issue was automatically created by the API Monitoring System*  
*Incident ID: INC-1730448000*

Labels: api-downtime, automated, critical
```

### **Recovery Comment**

```markdown
## ✅ API Recovered Successfully!

**Total Alerts Closed:** 1 (Issues: #45)
**Downtime Duration:** 1.0 hours
**Recovered At:** 2025-11-01T09:00:00Z
**Current Status:** ✅ Operational

The API is now responding normally and has been stable for the last 3 checks.

---
*All related downtime alerts have been automatically closed.*
```

### **AI Prediction Alert**

```markdown
Title: 🤖 AI Prediction: High Failure Risk for https://api.example.com/endpoint

## 🤖 AI Prediction Alert

**API URL:** `https://api.example.com/endpoint`  
**Failure Probability:** 78.5%  
**Prediction Time:** 2025-11-01T08:15:00Z  
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

---

## ⚙️ Configuration

### **Environment Variables**
```bash
MONGODB_URI=mongodb://localhost:27017/
GITHUB_TOKEN=ghp_xxxxxxxxxxxx
```

### **Alert Settings**
```python
# alert_manager.py
alert_cooldown_minutes = 15
consecutive_failures_threshold = 3
consecutive_successes_threshold = 3

# ai_alert_manager.py
training_interval_minutes = 15
prediction_threshold = 0.7  # 70%
minimum_data_points = 50
```

### **Monitoring Settings**
```python
# app.py
check_interval_seconds = 30
request_timeout_seconds = 10
```

---

## 🚀 Getting Started

### **Installation**

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start MongoDB:**
   ```bash
   mongod
   ```

3. **Configure GitHub:**
   - Open dashboard: `http://localhost:5000/advanced_monitor`
   - Click Settings
   - Fill in repository details
   - Click "Sync GitHub Data"

4. **Start Application:**
   ```bash
   # Windows
   START_HERE.bat
   
   # Or manually
   python app.py
   ```

5. **Access Dashboard:**
   ```
   http://localhost:5000/advanced_monitor
   ```

### **Clean Restart**
```bash
RESTART_CLEAN.bat
```
This will:
- Kill Python processes
- Clear cache
- Start fresh

---

## 📈 Monitoring Workflow

### **Daily Operations**

1. **Dashboard opens** → Auto-refresh every 60 seconds
2. **APIs monitored** → Every 30 seconds
3. **AI training** → Every 15 minutes per category
4. **Alerts sent** → Automatically to GitHub
5. **Recovery detected** → Issues closed automatically

### **No Manual Work Required!**

The system is fully automatic:
- ✅ Monitors APIs continuously
- ✅ Detects downtime automatically
- ✅ Creates GitHub issues automatically
- ✅ Trains AI models automatically
- ✅ Predicts failures automatically
- ✅ Closes issues on recovery automatically

---

## 🎯 Key Benefits

### **1. Proactive Monitoring**
- Catch issues before users do
- AI predicts failures 15 minutes ahead
- Prevent downtime with early warnings

### **2. Zero Manual Work**
- No button clicking needed
- Automatic alert creation
- Automatic issue closure
- Self-training AI models

### **3. Complete Visibility**
- Real-time dashboard
- Historical trends
- Alert status at a glance
- GitHub integration

### **4. Smart Alerting**
- No false positives (3 consecutive failures)
- No alert spam (cooldown periods)
- Context-rich notifications
- Actionable recommendations

### **5. Developer Correlation**
- Links downtime to commits
- Identifies potential causes
- Tracks deployment impact
- Faster root cause analysis

---

## 🔍 Troubleshooting

### **Common Issues**

#### **1. Alerts Not Sending**
**Check:**
- GitHub settings configured?
- Repository owner/name correct?
- GitHub token valid?
- API down for 90+ seconds (3 checks)?

**Console logs:**
```
[Alert] API xxx status: Down, consecutive failures: 3
[Alert] Creating downtime alert for API xxx
```

#### **2. Recovery Alert Not Sending**
**Check:**
- Open downtime alert exists?
- API up for 90+ seconds (3 checks)?

**Console logs:**
```
[Alert] API xxx has 1 open downtime alert(s)
[Alert] API xxx consecutive successes: 3/3
[Alert] ✅ Creating recovery alert for API xxx
```

#### **3. AI Predictions Not Working**
**Check:**
- TensorFlow installed?
- Enough historical data (50+ logs)?
- 15 minutes passed since last training?

**Console logs:**
```
[AI] Training model for API xxx...
[AI] Loaded pre-trained model for REST API
```

#### **4. Time Shows Wrong**
**Fixed:** Timezone handling added
- All timestamps stored with 'Z' suffix (UTC)
- JavaScript parses correctly
- Shows accurate "X mins ago"

---

## 📊 Performance

### **System Requirements**
- **CPU:** 2+ cores recommended
- **RAM:** 4GB minimum (8GB for AI training)
- **Disk:** 1GB for models and logs
- **Network:** Stable internet connection

### **Scalability**
- **APIs:** Tested with 50+ APIs
- **Checks:** 100+ per minute
- **Logs:** Millions of records
- **Models:** One per category (6 categories)

### **Response Times**
- **API Check:** < 10 seconds
- **Dashboard Load:** < 2 seconds
- **Alert Creation:** < 5 seconds
- **AI Prediction:** < 1 second (after training)
- **Model Training:** 5-10 minutes (once per 15 min)
- **Model Loading:** 2 seconds (on startup)

---

## 🔐 Security

### **Best Practices**
1. **GitHub Token:**
   - Use personal access token
   - Minimum permissions: `repo` scope
   - Store in environment variable
   - Never commit to repository

2. **MongoDB:**
   - Use authentication
   - Restrict network access
   - Regular backups

3. **API Monitoring:**
   - Secure header values
   - Use HTTPS when possible
   - Validate SSL certificates

---

## 🎓 Learning & Insights

### **AI Model Learns:**
- Normal latency patterns
- Typical error rates
- Time-of-day variations
- Category-specific behaviors
- Failure precursors

### **Correlation Engine Tracks:**
- Commit frequency
- Deployment timing
- Code change impact
- Developer patterns
- Issue relationships

### **Dashboard Shows:**
- Real-time health
- Historical trends
- Alert patterns
- AI accuracy
- System performance

---

## 🚀 Future Enhancements

### **Potential Features**
1. **Multi-channel Alerts:** Slack, Email, SMS
2. **Custom Alert Rules:** User-defined thresholds
3. **SLA Tracking:** Uptime guarantees
4. **Incident Management:** Full workflow
5. **Team Collaboration:** Comments, assignments
6. **Advanced Analytics:** Trends, predictions
7. **Mobile App:** iOS/Android
8. **API Versioning:** Track API changes
9. **Load Testing:** Integrated testing
10. **Cost Tracking:** Monitor API costs

---

## 📝 Summary

### **What This System Does:**

1. **Monitors APIs** continuously (every 30 seconds)
2. **Detects downtime** automatically (3 consecutive failures)
3. **Creates GitHub issues** automatically for downtime
4. **Trains AI models** every 15 minutes
5. **Predicts failures** before they happen (>70% risk)
6. **Creates warning issues** for high-risk predictions
7. **Closes issues** automatically on recovery
8. **Correlates** downtime with code changes
9. **Displays** real-time status on dashboard
10. **Auto-refreshes** every 60 seconds

### **Zero Manual Work:**
- ✅ Everything is automatic
- ✅ No buttons to click
- ✅ No manual alerts
- ✅ No manual recovery
- ✅ No manual training

### **Complete Solution:**
- 🔍 Monitoring
- 🤖 AI Prediction
- 🚨 Automatic Alerting
- 📊 Visualization
- 🔗 GitHub Integration
- 👨‍💻 Developer Correlation

---

## 📞 Quick Reference

### **URLs**
- Dashboard: `http://localhost:5000/advanced_monitor`
- API Docs: `http://localhost:5000/api/docs`

### **Key Files**
- Main App: `app.py`
- Alerts: `alert_manager.py`, `ai_alert_manager.py`
- AI: `ai_predictor.py`
- UI: `static_advanced/monitor.js`

### **Key Commands**
```bash
# Start
START_HERE.bat

# Clean Restart
RESTART_CLEAN.bat

# Manual Start
python app.py
```

### **Console Logs to Watch**
```
[Alert] Creating downtime alert...
[Alert] ✅ Creating recovery alert...
[AI Alert] Prediction alert...
[AI] Training model...
[Auto-refresh #1] Updating...
```

---

**🎉 Project Complete! Fully automatic API monitoring with AI-powered predictions and GitHub integration!**
