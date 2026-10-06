# 🎨 Alert Status UI - Real-Time Display

## ✅ What's Implemented

### **Live Alert Status on Each API Card**

Shows real-time information about:
1. **Downtime Alerts** - When alert was sent
2. **AI Predictions** - Current failure risk percentage
3. **Time Information** - How long ago events occurred
4. **GitHub Links** - Direct links to issues

---

## 🎯 What You'll See

### **Scenario 1: API is Healthy**
```
┌─────────────────────────────────────┐
│ https://api.example.com/endpoint    │
│ Status: ✅ Up                       │
│ [🤖 AI Insights]                    │
│ 🤖 AI: 15% risk - Good (2 mins ago)│ ← Green
└─────────────────────────────────────┘
```

### **Scenario 2: API Down - Alert Sent**
```
┌─────────────────────────────────────┐
│ https://api.example.com/endpoint    │
│ Status: ❌ Down                     │
│ [🤖 AI Insights]                    │
│ 🚨 Alert sent 5 mins ago #45        │ ← Red with link
│ 🤖 AI: 85% risk - Bad (2 mins ago) │ ← Red
└─────────────────────────────────────┘
```

### **Scenario 3: AI Predicts High Risk**
```
┌─────────────────────────────────────┐
│ https://api.example.com/endpoint    │
│ Status: ✅ Up                       │
│ [🤖 AI Insights]                    │
│ 🤖 AI: 78% failure risk (1 min ago)│ ← Red
│     #50                             │ ← Link to AI prediction issue
└─────────────────────────────────────┘
```

### **Scenario 4: No Data Yet**
```
┌─────────────────────────────────────┐
│ https://api.example.com/endpoint    │
│ Status: ✅ Up                       │
│ [🤖 AI Insights]                    │
│ 🤖 AI monitoring active             │ ← Blue
└─────────────────────────────────────┘
```

---

## 📊 Status Colors

| Status | Color | Meaning |
|--------|-------|---------|
| 🤖 AI: <30% risk - Good | Green (#3FB950) | Low failure risk |
| 🤖 AI monitoring active | Blue (#58A6FF) | Monitoring, no prediction yet |
| 🤖 AI: >70% risk | Red (#F85149) | High failure risk |
| 🚨 Alert sent | Red (#F85149) | Downtime alert active |

---

## ⏰ Time Display

### **Examples:**
- `just now` - Less than 1 minute
- `2 mins ago` - 2 minutes
- `1 hour ago` - 1 hour
- `3 hours ago` - 3 hours
- `2 days ago` - 2 days

---

## 🔗 GitHub Issue Links

### **Clickable Links:**
```html
🚨 Alert sent 5 mins ago #45
                        ↑
                  Clickable link to GitHub issue
```

**Clicking opens:** `https://github.com/user/repo/issues/45`

---

## 📡 How It Works

### **Backend API:**
```
GET /api/alert-status/<api_id>

Response:
{
  "downtime_alert": {
    "created_at": "2025-11-01T08:30:00Z",
    "github_issue_number": 45,
    "github_issue_url": "https://github.com/user/repo/issues/45",
    "reason": "API Error: 3 consecutive failures detected"
  },
  "ai_prediction": {
    "failure_probability": 0.85,
    "last_check": "2025-11-01T08:32:00Z",
    "github_issue_number": 50,
    "github_issue_url": "https://github.com/user/repo/issues/50"
  }
}
```

### **Frontend:**
1. Renders monitor cards
2. Calls `/api/alert-status/<api_id>` for each API
3. Updates status div with real-time info
4. Shows color-coded status
5. Adds clickable GitHub links

---

## 🎨 UI Components

### **Alert Status Div:**
```html
<div id="alert-status-{api_id}" class="auto-alert-status">
  <!-- Dynamically updated content -->
</div>
```

### **Content Examples:**

**Downtime Alert:**
```html
<div style="color: #F85149;">
  🚨 Alert sent 5 mins ago 
  <a href="https://github.com/user/repo/issues/45" target="_blank" style="color: #58A6FF;">
    #45
  </a>
</div>
```

**AI Prediction (Good):**
```html
<div style="color: #3FB950;">
  🤖 AI: 15% risk - Good (2 mins ago)
</div>
```

**AI Prediction (Bad):**
```html
<div style="color: #F85149;">
  🤖 AI: 85% failure risk (1 min ago)
  <a href="https://github.com/user/repo/issues/50" target="_blank" style="color: #58A6FF;">
    #50
  </a>
</div>
```

---

## 🔄 Auto-Refresh

### **Status updates automatically when:**
- Page loads
- Monitor list refreshes
- User navigates back to dashboard

### **To force refresh:**
- Reload page (F5)
- Status updates every time monitors are fetched

---

## 📊 Real-World Examples

### **Example 1: Healthy API**
```
API: https://api.stripe.com/v1/charges
Status: ✅ Up
Alert Status:
  🤖 AI: 12% risk - Good (2 mins ago)
```

### **Example 2: API Just Went Down**
```
API: https://api.example.com/payment
Status: ❌ Down
Alert Status:
  🚨 Alert sent just now #45
  🤖 AI: 95% risk - Bad (1 min ago) #50
```

### **Example 3: API Recovering**
```
API: https://api.example.com/payment
Status: ✅ Up
Alert Status:
  🤖 AI: 25% risk - Good (just now)
  
Note: Downtime alert closed automatically
```

### **Example 4: AI Predicts Issue**
```
API: https://api.example.com/users
Status: ✅ Up (still working!)
Alert Status:
  🤖 AI: 78% failure risk (14 mins ago) #52
  
Warning: API might fail soon based on patterns
```

---

## 🎯 Benefits

### **For Users:**
- ✅ **See alert status at a glance**
- ✅ **Know when alerts were sent**
- ✅ **Click to view GitHub issues**
- ✅ **See AI predictions in real-time**

### **For Teams:**
- ✅ **Track alert history**
- ✅ **Monitor AI accuracy**
- ✅ **Quick access to GitHub**
- ✅ **Understand system health**

---

## 🚀 To Use

### **1. Restart Flask:**
```bash
python app.py
```

### **2. Open Dashboard:**
```
http://localhost:5000/advanced_monitor
```

### **3. View Alert Status:**
- Each API card shows live status
- Colors indicate severity
- Links open GitHub issues
- Time shows how recent

---

## 📝 Status Messages

### **All Possible Messages:**

| Message | Meaning | Color |
|---------|---------|-------|
| `🤖 AI monitoring active` | No prediction yet | Blue |
| `🤖 AI: X% risk - Good` | Low risk (< 70%) | Green |
| `🤖 AI: X% failure risk` | High risk (≥ 70%) | Red |
| `🚨 Alert sent X ago #N` | Downtime alert active | Red |
| `Loading alert status...` | Fetching data | Gray |
| `Alert status unavailable` | API error | Gray |

---

## ✅ Summary

### **What You Get:**

1. **Real-Time Status**
   - See alerts as they're sent
   - AI predictions update every 15 mins
   - Time shows how recent

2. **Visual Indicators**
   - Green = Good (low risk)
   - Blue = Monitoring
   - Red = Alert/High risk

3. **GitHub Integration**
   - Click issue numbers
   - Opens in new tab
   - Direct access to details

4. **Smart Display**
   - Shows most important info
   - Color-coded for quick scanning
   - Updates automatically

**Refresh browser and see live alert status on all APIs!** 🎉
