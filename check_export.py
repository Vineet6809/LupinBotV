#!/usr/bin/env python3
"""
Check if project is ready for export to Replit
"""

import os
import sys
from pathlib import Path

def check_export_readiness():
    """Check if all files are ready for Replit export."""
    
    print("Checking export readiness...\n")
    
    required_files = [
        'main.py',
        'pyproject.toml',
        'database.py',
        'dashboard.py',
        'cache.py',
        'gemini.py',
        'start_dashboard.py',
        'cogs/streaks.py',
        'cogs/fun.py',
        'cogs/challenges.py',
        'cogs/moderation.py',
        'cogs/utilities.py',
        'templates/dashboard.html',
        '.gitignore',
        'REPLIT_DEPLOYMENT.md',
        'EXPORT_README.md'
    ]
    
    optional_files = [
        '.replit',
        'replit.nix',
        'api/dashboard.py',
        'vercel.json'
    ]
    
    missing_files = []
    found_files = []
    optional_found = []
    
    # Check required files
    for file in required_files:
        if os.path.exists(file):
            found_files.append(file)
            print(f"[OK] {file}")
        else:
            missing_files.append(file)
            print(f"[MISSING] {file} - MISSING")
    
    # Check optional files
    print("\nOptional files:")
    for file in optional_files:
        if os.path.exists(file):
            optional_found.append(file)
            print(f"[OPT] {file}")
    
    # Check files that should NOT be exported
    print("\n[WARN] Files that should NOT be exported:")
    sensitive_files = [
        '.env',
        'database.db',
        'bot.log'
    ]
    
    for file in sensitive_files:
        if os.path.exists(file):
            print(f"[WARN] {file} - Make sure this is in .gitignore!")
        else:
            print(f"[OK] {file} - Not found (good)")
    
    # Summary
    print("\n" + "="*50)
    print("Summary:")
    print(f"[OK] Found: {len(found_files)}/{len(required_files)} required files")
    print(f"[OPT] Optional: {len(optional_found)} files")
    
    if missing_files:
        print("\n[MISSING] Missing files:")
        for file in missing_files:
            print(f"   - {file}")
        print("\n[WARN] Please add missing files before exporting!")
        return False
    else:
        print("\n[OK] All required files present!")
        print("[OK] Ready for export to Replit!")
        return True

def check_gitignore():
    """Check if .gitignore includes necessary patterns."""
    if not os.path.exists('.gitignore'):
        print("[WARN] .gitignore not found!")
        return False
    
    with open('.gitignore', 'r', encoding='utf-8') as f:
        content = f.read()
    
    required_patterns = [
        '.env',
        '__pycache__',
        'database.db',
        '*.log',
        '.DS_Store'
    ]
    
    print("\nChecking .gitignore:")
    all_found = True
    for pattern in required_patterns:
        if pattern in content:
            print(f"[OK] {pattern}")
        else:
            print(f"[WARN] {pattern} - Not in .gitignore")
            all_found = False
    
    return all_found

def main():
    """Main function."""
    print("LupinBot Export Readiness Check\n")
    print("="*50)
    
    # Check files
    files_ready = check_export_readiness()
    
    # Check .gitignore
    gitignore_ready = check_gitignore()
    
    # Final verdict
    print("\n" + "="*50)
    if files_ready and gitignore_ready:
        print("\n[SUCCESS] PROJECT IS READY FOR EXPORT!")
        print("\nNext steps:")
        print("1. Review this checklist")
        print("2. Read EXPORT_README.md for export instructions")
        print("3. Read REPLIT_DEPLOYMENT.md for deployment guide")
        print("4. Export to Replit!")
        return 0
    else:
        print("\n[WARN] PROJECT NEEDS ATTENTION")
        print("\nPlease:")
        if not files_ready:
            print("- Add missing files")
        if not gitignore_ready:
            print("- Update .gitignore")
        print("- Run this check again")
        return 1

if __name__ == '__main__':
    sys.exit(main())

