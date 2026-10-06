#!/usr/bin/env python3
"""
Friend's Improvements Integration Script
Automatically merges your friend's improvements into your current project
"""

import os
import shutil
import json
from pathlib import Path

class ImprovementIntegrator:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.friend_dir = self.project_root / "friend"
        self.src_dir = self.project_root / "src"
        self.static_dir = self.project_root / "static_advanced"
        self.scripts_dir = self.project_root / "scripts"
        
    def backup_current_system(self):
        """Backup current system before integration"""
        print("🔄 Creating backup of current system...")
        backup_dir = self.project_root / f"backup_{int(time.time())}"
        
        # Backup key files
        files_to_backup = [
            "src/app.py",
            "src/ai_predictor.py", 
            "static_advanced/monitor.js",
            "static_advanced/monitor.html",
            "static_advanced/monitor.css",
            ".env"
        ]
        
        backup_dir.mkdir(exist_ok=True)
        for file_path in files_to_backup:
            src = self.project_root / file_path
            if src.exists():
                dst = backup_dir / file_path
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                print(f"✅ Backed up: {file_path}")
        
        print(f"📦 Backup created at: {backup_dir}")
        return backup_dir
    
    def integrate_security_modules(self):
        """Integrate security and authentication modules"""
        print("🔐 Integrating security modules...")
        
        security_files = [
            ("friend/src/auth_manager.py", "src/auth_manager.py"),
            ("friend/src/security_manager.py", "src/security_manager.py"),
        ]
        
        for src_file, dst_file in security_files:
            src_path = self.project_root / src_file
            dst_path = self.project_root / dst_file
            
            if src_path.exists():
                shutil.copy2(src_path, dst_path)
                print(f"✅ Integrated: {dst_file}")
    
    def integrate_enhanced_ai(self):
        """Integrate enhanced AI features"""
        print("🤖 Integrating enhanced AI features...")
        
        ai_files = [
            ("friend/src/ai_predictor.py", "src/ai_predictor_friend.py"),  # Keep as backup
            ("friend/src/process_task_manager.py", "src/process_task_manager.py"),
            ("friend/src/ai_training_service.py", "src/ai_training_service_friend.py"),
        ]
        
        for src_file, dst_file in ai_files:
            src_path = self.project_root / src_file
            dst_path = self.project_root / dst_file
            
            if src_path.exists():
                shutil.copy2(src_path, dst_path)
                print(f"✅ Integrated: {dst_file}")
        
        # Copy training scripts
        training_scripts = [
            "friend/scripts/train_lstm.py",
            "friend/scripts/train_category_models.py", 
            "friend/scripts/train_model.py",
            "friend/scripts/compare_models.py"
        ]
        
        self.scripts_dir.mkdir(exist_ok=True)
        for script in training_scripts:
            src_path = self.project_root / script
            dst_path = self.scripts_dir / Path(script).name
            
            if src_path.exists():
                shutil.copy2(src_path, dst_path)
                print(f"✅ Integrated script: {Path(script).name}")
    
    def integrate_self_healing(self):
        """Integrate self-healing capabilities"""
        print("🔧 Integrating self-healing capabilities...")
        
        healing_file = "friend/src/self_healing.py"
        src_path = self.project_root / healing_file
        dst_path = self.src_dir / "self_healing.py"
        
        if src_path.exists():
            shutil.copy2(src_path, dst_path)
            print(f"✅ Integrated: self_healing.py")
    
    def integrate_github_features(self):
        """Integrate GitHub integration features"""
        print("🔗 Integrating GitHub features...")
        
        github_files = [
            ("friend/src/github_integration.py", "src/github_integration.py"),
            ("friend/src/issue_integration.py", "src/issue_integration.py"),
        ]
        
        for src_file, dst_file in github_files:
            src_path = self.project_root / src_file
            dst_path = self.project_root / dst_file
            
            if src_path.exists():
                shutil.copy2(src_path, dst_path)
                print(f"✅ Integrated: {dst_file}")
    
    def integrate_enhanced_frontend(self):
        """Integrate enhanced frontend features"""
        print("🎨 Integrating enhanced frontend features...")
        
        frontend_files = [
            ("friend/static_advanced/monitor_pro.css", "static_advanced/monitor_pro.css"),
            ("friend/static_advanced/ai_showcase.html", "static_advanced/ai_showcase.html"),
        ]
        
        for src_file, dst_file in frontend_files:
            src_path = self.project_root / src_file
            dst_path = self.project_root / dst_file
            
            if src_path.exists():
                shutil.copy2(src_path, dst_path)
                print(f"✅ Integrated: {dst_file}")
    
    def update_environment_config(self):
        """Update .env file with new configuration options"""
        print("⚙️ Updating environment configuration...")
        
        env_file = self.project_root / ".env"
        new_config = """
# Friend's Improvements Configuration
JWT_SECRET_KEY=your_jwt_secret_key_here_change_this
ENCRYPTION_KEY=your_32_character_encryption_key

# GitHub Integration
GITHUB_TOKEN=your_github_personal_access_token
GITHUB_REPO=your-org/your-repo

# Self-Healing
ENABLE_SELF_HEALING=true
HEALING_CHECK_INTERVAL=60

# Enhanced AI
AI_MODEL_PATH=models/
ENABLE_PROCESS_BASED_TRAINING=true
AI_CONFIDENCE_THRESHOLD=0.7

# Security
ENABLE_AUTHENTICATION=false
SESSION_TIMEOUT=3600
"""
        
        if env_file.exists():
            with open(env_file, "a", encoding="utf-8") as f:
                f.write(new_config)
            print("✅ Updated .env with new configuration")
        else:
            print("⚠️ .env file not found, please create it manually")
    
    def create_integration_guide(self):
        """Create a step-by-step integration guide"""
        guide = """
# 🚀 Integration Guide - Friend's Improvements

## 📋 Next Steps:

### 1. Update your main app.py
Add these imports to the top of your src/app.py:

```python
# Friend's improvements
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
```

### 2. Update your email alert system
Enhance your send_api_down_alert function to include GitHub integration.

### 3. Test the integration
- Start with security modules
- Test AI predictions
- Enable self-healing
- Add GitHub integration

### 4. Update database schema
Add new collections for users, security, healing logs, and GitHub sync.

## 🎯 Priority Order:
1. Security Manager (Immediate)
2. Enhanced AI Predictor (High)
3. Self-Healing (High)
4. GitHub Integration (Medium)
5. Enhanced Frontend (Low)

## ⚠️ Important:
- Keep backups of your original files
- Test each module individually
- Update configuration step by step
- Monitor system performance during integration
"""
        
        guide_file = self.project_root / "INTEGRATION_GUIDE.md"
        with open(guide_file, "w", encoding="utf-8") as f:
            f.write(guide)
        
        print(f"📖 Created integration guide: {guide_file}")
    
    def run_full_integration(self):
        """Run the complete integration process"""
        print("🚀 Starting full integration of friend's improvements...")
        print("=" * 60)
        
        try:
            # Step 1: Backup
            backup_dir = self.backup_current_system()
            
            # Step 2: Integrate modules in order
            self.integrate_security_modules()
            self.integrate_enhanced_ai()
            self.integrate_self_healing()
            self.integrate_github_features()
            self.integrate_enhanced_frontend()
            
            # Step 3: Update configuration
            self.update_environment_config()
            
            # Step 4: Create guide
            self.create_integration_guide()
            
            print("=" * 60)
            print("🎉 Integration completed successfully!")
            print(f"📦 Backup available at: {backup_dir}")
            print("📖 Follow INTEGRATION_GUIDE.md for next steps")
            print("⚠️ Remember to test each module before full deployment")
            
        except Exception as e:
            print(f"❌ Integration failed: {e}")
            print("📦 Check your backup directory for original files")

if __name__ == "__main__":
    import time
    
    integrator = ImprovementIntegrator()
    
    print("🔧 Friend's Improvements Integration Tool")
    print("This will merge your friend's improvements into your current project")
    print()
    
    response = input("Do you want to continue? (y/N): ")
    if response.lower() == 'y':
        integrator.run_full_integration()
    else:
        print("Integration cancelled. Your files remain unchanged.")
