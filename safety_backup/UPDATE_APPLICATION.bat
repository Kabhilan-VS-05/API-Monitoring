@echo off
echo ========================================
echo 🔧 Application Update Script
echo ========================================
echo.
echo This script will update the main application files
echo to integrate friend improvements and remove references
echo to deleted files.
echo.
pause

echo 🔄 Updating application files...
echo.

:: Update app.py to remove friend file references
echo [1/5] Updating src\app.py...
python -c "
import re
import os

app_file = 'src\app.py'
if os.path.exists(app_file):
    with open(app_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remove friend file imports
    content = re.sub(r'from ai_predictor_friend import.*\n?', '', content)
    content = re.sub(r'from ai_training_service_friend import.*\n?', '', content)
    
    # Add proper imports for integrated features
    imports_to_add = '''# Friend's improvements - now integrated
try:
    from auth_manager import create_user, authenticate, create_access_token, role_required
except Exception:
    create_user = authenticate = create_access_token = role_required = None

try:
    from security_manager import decrypt_if_needed
except Exception:
    def decrypt_if_needed(value):
        return value

try:
    from self_healing import SelfHealingManager
except Exception:
    SelfHealingManager = None

try:
    from github_integration import GitHubIntegration
except Exception:
    GitHubIntegration = None

try:
    from issue_integration import IssueIntegration
except Exception:
    IssueIntegration = None

'''
    
    # Insert imports after existing imports
    if 'from flask import' in content and 'Friend\\'s improvements' not in content:
        flask_pos = content.find('from flask import')
        end_of_imports = content.find('\n\n', flask_pos)
        if end_of_imports != -1:
            content = content[:end_of_imports] + '\n\n' + imports_to_add + content[end_of_imports:]
    
    with open(app_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print('   Updated: src\\app.py')
else:
    print('   Skipped: src\\app.py not found')
"

:: Update ai_training_service.py to remove friend references
echo [2/5] Updating src\ai_training_service.py...
python -c "
import re
import os

service_file = 'src\ai_training_service.py'
if os.path.exists(service_file):
    with open(service_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remove friend references
    content = re.sub(r'ai_predictor_friend', 'ai_predictor', content)
    
    with open(service_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print('   Updated: src\\ai_training_service.py')
else:
    print('   Skipped: src\\ai_training_service.py not found')
"

:: Clean up .env file
echo [3/5] Cleaning up .env file...
if exist ".env" (
    python -c "
import re

with open('.env', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove duplicate entries and clean up
lines = content.split('\n')
seen = set()
clean_lines = []

for line in lines:
    if '=' in line:
        key = line.split('=')[0].strip()
        if key not in seen:
            seen.add(key)
            clean_lines.append(line)
    else:
        clean_lines.append(line)

with open('.env', 'w', encoding='utf-8') as f:
    f.write('\n'.join(clean_lines))

print('   Cleaned: .env file')
"
) else (
    echo   Skipped: .env file not found
)

:: Update requirements.txt if needed
echo [4/5] Checking requirements.txt...
if exist "requirements.txt" (
    python -c "
with open('requirements.txt', 'r') as f:
    lines = f.readlines()

# Remove duplicates and ensure proper format
unique_lines = []
seen = set()

for line in lines:
    line = line.strip()
    if line and line not in seen:
        seen.add(line)
        unique_lines.append(line)

with open('requirements.txt', 'w') as f:
    f.write('\n'.join(unique_lines) + '\n')

print('   Checked: requirements.txt')
"
)

:: Create updated README
echo [5/5] Creating updated README...
python -c "
readme_content = '''# 🤖 Proactive AI Co-Pilot for Predictive API Monitoring

An AI-powered system that predicts API failures, provides root cause analysis, and gives developer insights by correlating API performance with GitHub commits, pull requests, and issues.

## 🌟 Features

### 🔮 AI-Powered Predictions
- **Failure Prediction**: Machine learning models predict API failures before they happen
- **Risk Scoring**: 0-100 risk assessment for each monitored API
- **Anomaly Detection**: Real-time detection of unusual patterns in API behavior
- **Pattern Recognition**: Identifies recurring issues and trends

### 📊 Advanced Monitoring
- **Real-time API Monitoring**: Continuous health checks with configurable intervals
- **Latency Tracking**: DNS, TCP, TLS, server processing, and download time breakdown
- **Uptime Metrics**: 24-hour uptime percentage tracking
- **TLS Certificate Monitoring**: Expiry alerts and security checks

### 🔗 GitHub Integration
- **Commit Synchronization**: Automatically syncs repository commits
- **Pull Request Tracking**: Monitors PR activity and correlates with API performance
- **Issue Management**: Syncs and tracks GitHub issues
- **Data Correlation**: Links API failures to code changes

### 🔐 Security Features
- **Authentication**: User management and access control
- **Data Encryption**: Encrypted storage for sensitive data
- **Role-Based Access**: Different permission levels for users

### 🔧 Self-Healing
- **Automatic Recovery**: Service restart capabilities
- **Health Monitoring**: Proactive system health checks
- **Fallback Systems**: Automatic failover mechanisms

## 🛠️ Tech Stack

- **Backend**: Python, Flask
- **Database**: MongoDB
- **AI/ML**: TensorFlow, scikit-learn, NumPy
- **Frontend**: HTML5, CSS3, JavaScript, Chart.js
- **APIs**: GitHub REST API, PyCURL for HTTP monitoring
- **Security**: JWT authentication, data encryption

## 📦 Installation

### Prerequisites
- Python 3.8+
- MongoDB 4.0+
- Git

### Quick Setup

1. **Clone and setup**
```bash
git clone <repository-url>
cd API-Downtime
pip install -r requirements.txt
```

2. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Start MongoDB**
```bash
# Windows
net start MongoDB

# Linux/Mac
sudo systemctl start mongod
```

4. **Run the application**
```bash
python src/app.py
```

5. **Access the dashboard**
- Simple Dashboard: http://localhost:5000
- Advanced Dashboard: http://localhost:5000/advanced_monitor

## 🚀 Usage

### Add an API to Monitor
1. Click "Add API" button
2. Enter API URL and configuration
3. Set check frequency and notification settings
4. Click "Save"

### Configure GitHub Integration
1. Click settings icon (⚙️)
2. Enter repository details and GitHub token
3. Set sync period
4. Click "Sync GitHub Data"

### View AI Insights
1. Click "🤖 AI Insights" on any monitored API
2. View predictions, risk scores, and recommendations

## 🧠 AI Models

### Enhanced Category-Aware Models
- **LSTM Networks**: Time-series prediction for latency trends
- **Autoencoder**: Anomaly detection for unusual patterns
- **Category-Specific Training**: Separate models for different API types
- **Process-Based Training**: Isolated training processes for better performance

## 📊 MongoDB Collections

- `monitored_apis` - API configurations
- `monitoring_logs` - Check results and history
- `git_commits` - Synced GitHub commits
- `issues` - GitHub issues
- `incident_reports` - Incident tracking
- `users` - User authentication data
- `ai_training_runs` - AI model training history

## 🔧 Configuration

### Environment Variables
```env
# Database
MONGODB_URI=mongodb://localhost:27017/
DATABASE_NAME=api_monitoring

# GitHub Integration
GITHUB_TOKEN=your_github_personal_access_token
GITHUB_REPO=your-org/your-repo

# Email Notifications
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_app_password

# Security
JWT_SECRET_KEY=your_jwt_secret_key
ENCRYPTION_KEY=your_32_character_encryption_key

# AI Features
AI_MODEL_PATH=models/
ENABLE_PROCESS_BASED_TRAINING=true
AI_CONFIDENCE_THRESHOLD=0.7

# Self-Healing
ENABLE_SELF_HEALING=true
HEALING_CHECK_INTERVAL=60
```

## 🧪 Testing

```bash
# Run all tests
python -m pytest tests/

# Run specific test
python -m pytest tests/test_ai.py

# Run with coverage
python -m pytest --cov=. tests/
```

## 📁 Project Structure

```
API Downtime/
├── src/                    # Source code
├── static/                 # Basic frontend
├── static_advanced/        # Advanced dashboard
├── models/                 # AI models organized by type
├── scripts/                # Training and utility scripts
├── docs/                   # Documentation
├── tests/                  # Test files
└── running API/            # Test API server
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License.

---

**Made with ❤️ for better API monitoring**
'''

with open('README.md', 'w', encoding='utf-8') as f:
    f.write(readme_content)

print('   Updated: README.md')
"

echo.
echo ✅ Application update completed!
echo.
echo 🚀 Next steps:
echo   1. Test the application: python src\app.py
echo   2. Check for any import errors
echo   3. Verify all functionality works
echo   4. Commit changes to git
echo.
pause
