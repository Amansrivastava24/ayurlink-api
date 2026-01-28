#!/usr/bin/env python3
"""
Quick deployment setup script for AyurLink API
This script helps you prepare your project for deployment
"""

import os
import sys
import subprocess

def check_file_exists(filepath):
    """Check if a file exists"""
    return os.path.exists(filepath)

def create_gitignore():
    """Create or update .gitignore file"""
    gitignore_content = """# Environment variables
.env
.env.local

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Database
*.db
*.sqlite3

# Logs
*.log
"""
    with open('.gitignore', 'w') as f:
        f.write(gitignore_content)
    print("✅ Created .gitignore file")

def main():
    print("🚀 AyurLink API Deployment Setup")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not check_file_exists('app/main.py'):
        print("❌ Error: Please run this script from the project root directory")
        sys.exit(1)
    
    print("\n📋 Checking deployment files...")
    
    # Check required files
    required_files = {
        'requirements.txt': '✅ Found',
        'Procfile': '✅ Found',
        '.env.example': '✅ Found',
        'runtime.txt': '✅ Found'
    }
    
    for file, status in required_files.items():
        if check_file_exists(file):
            print(f"  {status} {file}")
        else:
            print(f"  ❌ Missing {file}")
    
    # Create .gitignore
    print("\n📝 Creating .gitignore...")
    create_gitignore()
    
    # Check if git is initialized
    print("\n🔍 Checking Git repository...")
    if not check_file_exists('.git'):
        print("  ⚠️  Git not initialized. Run: git init")
    else:
        print("  ✅ Git repository found")
    
    print("\n" + "=" * 50)
    print("✅ Deployment setup complete!")
    print("\n📖 Next steps:")
    print("  1. Review the DEPLOYMENT_GUIDE.md file")
    print("  2. Choose a deployment platform (Render, Railway, Fly.io)")
    print("  3. Push your code to GitHub")
    print("  4. Follow the platform-specific instructions")
    print("\n🎯 Recommended: Start with Render (easiest for beginners)")

if __name__ == "__main__":
    main()
