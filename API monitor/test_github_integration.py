"""
Test script for GitHub Integration
Run this to verify your GitHub integration is working correctly
"""

import os
import sys
from pymongo import MongoClient
from github_integration import GitHubIntegration
from issue_integration import IssueIntegration

def test_github_integration():
    """Test GitHub integration with sample repository"""
    
    print("=" * 60)
    print("GitHub Integration Test")
    print("=" * 60)
    
    # Check for GitHub token
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        print("\n❌ ERROR: GITHUB_TOKEN not found in environment variables")
        print("\nPlease set your GitHub token:")
        print("  1. Copy .env.example to .env")
        print("  2. Add your token: GITHUB_TOKEN=your_token_here")
        print("  3. Restart this script")
        return False
    
    print(f"\n✅ GitHub token found: {github_token[:10]}...")
    
    # Connect to MongoDB
    try:
        mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
        client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
        db = client[os.getenv("DATABASE_NAME", "api_monitoring")]
        client.server_info()  # Test connection
        print(f"✅ MongoDB connected: {mongodb_uri}")
    except Exception as e:
        print(f"\n❌ ERROR: Could not connect to MongoDB: {e}")
        print("\nPlease ensure MongoDB is running:")
        print("  - Start MongoDB service")
        print("  - Check connection string in .env")
        return False
    
    # Test repository details
    repo_owner = input("\nEnter GitHub repository owner (e.g., Kabhilan-VS-05): ").strip()
    repo_name = input("Enter GitHub repository name (e.g., API-Monitoring): ").strip()
    
    if not repo_owner or not repo_name:
        print("\n❌ ERROR: Repository owner and name are required")
        return False
    
    print(f"\n📦 Testing repository: {repo_owner}/{repo_name}")
    
    # Test GitHub Integration
    print("\n" + "-" * 60)
    print("Testing GitHub Integration (Commits & PRs)")
    print("-" * 60)
    
    try:
        github = GitHubIntegration(github_token, db)
        
        # Fetch commits
        print("\n🔄 Fetching commits (last 7 days)...")
        commit_result = github.fetch_commits(repo_owner, repo_name, since_days=7)
        
        if commit_result.get("success"):
            print(f"✅ Successfully fetched {commit_result['count']} commits")
        else:
            print(f"❌ Failed to fetch commits: {commit_result.get('error')}")
            return False
        
        # Fetch pull requests
        print("\n🔄 Fetching pull requests...")
        pr_result = github.fetch_pull_requests(repo_owner, repo_name)
        
        if pr_result.get("success"):
            print(f"✅ Successfully fetched {pr_result['count']} pull requests")
        else:
            print(f"❌ Failed to fetch PRs: {pr_result.get('error')}")
            return False
        
    except Exception as e:
        print(f"\n❌ ERROR in GitHub Integration: {e}")
        return False
    
    # Test Issue Integration
    print("\n" + "-" * 60)
    print("Testing Issue Integration")
    print("-" * 60)
    
    try:
        issue_integration = IssueIntegration(github_token, db)
        
        print("\n🔄 Fetching issues...")
        issue_result = issue_integration.fetch_github_issues(repo_owner, repo_name)
        
        if issue_result.get("success"):
            print(f"✅ Successfully fetched {issue_result['count']} issues")
        else:
            print(f"❌ Failed to fetch issues: {issue_result.get('error')}")
            return False
        
    except Exception as e:
        print(f"\n❌ ERROR in Issue Integration: {e}")
        return False
    
    # Verify data in MongoDB
    print("\n" + "-" * 60)
    print("Verifying Data in MongoDB")
    print("-" * 60)
    
    try:
        commit_count = db.git_commits.count_documents({})
        pr_count = db.pull_requests.count_documents({})
        issue_count = db.issues.count_documents({})
        
        print(f"\n📊 Database Statistics:")
        print(f"  - Commits: {commit_count}")
        print(f"  - Pull Requests: {pr_count}")
        print(f"  - Issues: {issue_count}")
        
        if commit_count > 0 or pr_count > 0 or issue_count > 0:
            print("\n✅ Data successfully stored in MongoDB!")
        else:
            print("\n⚠️  Warning: No data found in MongoDB")
            print("   This might be normal if the repository has no recent activity")
        
    except Exception as e:
        print(f"\n❌ ERROR verifying MongoDB data: {e}")
        return False
    
    # Success!
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED!")
    print("=" * 60)
    print("\nYour GitHub integration is working correctly!")
    print("\nNext steps:")
    print("  1. Start the Flask application: python app.py")
    print("  2. Open the Advanced Dashboard")
    print("  3. Click the Settings icon (⚙️)")
    print("  4. Enter your repository details")
    print("  5. Click 'Sync GitHub Data'")
    print("\n")
    
    return True

if __name__ == "__main__":
    try:
        # Load environment variables from .env file if it exists
        try:
            from dotenv import load_dotenv
            load_dotenv()
            print("✅ Loaded environment variables from .env file")
        except ImportError:
            print("⚠️  python-dotenv not installed. Using system environment variables.")
            print("   Install with: pip install python-dotenv")
        
        success = test_github_integration()
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
