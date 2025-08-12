#!/usr/bin/env python3
"""
Universal Import Fixer - يحل كل مشاكل الـ imports تلقائياً
"""

import os
import re
import subprocess
import sys
from pathlib import Path

class ImportFixer:
    def __init__(self):
        self.fixes_applied = 0
        self.errors_found = []

        # Common import fixes
        self.import_replacements = {
            'from src.models.subscription import Subscription': 'from src.models.subscription import SubscriptionPlan as Subscription',
            'from src.models.subscription import subscription': 'from src.models.subscription import SubscriptionPlan as Subscription',
        }

        # Required packages that need auto-installation
        self.required_packages = {
            'PIL': 'Pillow',
            'openai': 'openai',
            'cv2': 'opencv-python',
            'sklearn': 'scikit-learn',
            'requests': 'requests',
            'flask': 'flask',
            'numpy': 'numpy',
            'pandas': 'pandas',
        }

        # Typing imports
        self.typing_imports = ['List', 'Dict', 'Optional', 'Union', 'Tuple', 'Any', 'Set']

    def install_missing_packages(self):
        """Install missing packages automatically"""
        print("🔍 Checking for missing packages...")

        for import_name, package_name in self.required_packages.items():
            try:
                __import__(import_name)
                print(f"✓ {package_name} already installed")
            except ImportError:
                print(f"📦 Installing {package_name}...")
                try:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
                    print(f"✅ {package_name} installed successfully")
                except Exception as e:
                    print(f"❌ Failed to install {package_name}: {e}")

    def fix_typing_imports(self, content, filepath):
        """Add missing typing imports"""
        needs_typing = any(f': {t}' in content or f'-> {t}' in content 
                          for t in self.typing_imports)

        if needs_typing and 'from typing import' not in content:
            lines = content.split('\n')

            # Find where to insert (after existing imports)
            insert_pos = 0
            for i, line in enumerate(lines):
                if line.strip().startswith('import ') or line.strip().startswith('from '):
                    insert_pos = i + 1

            # Insert typing import
            typing_line = 'from typing import List, Dict, Optional, Union, Tuple, Any'
            lines.insert(insert_pos, typing_line)

            print(f"🔧 Added typing imports to {filepath}")
            self.fixes_applied += 1
            return '\n'.join(lines)

        return content

    def fix_import_statements(self, content, filepath):
        """Fix specific import statement issues"""
        original_content = content

        for old_import, new_import in self.import_replacements.items():
            if old_import in content:
                content = content.replace(old_import, new_import)
                print(f"🔧 Fixed import in {filepath}: {old_import} -> {new_import}")
                self.fixes_applied += 1

        return content

    def scan_and_fix_file(self, filepath):
        """Scan and fix a single Python file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            original_content = content

            # Apply fixes
            content = self.fix_typing_imports(content, filepath)
            content = self.fix_import_statements(content, filepath)

            # Save if modified
            if content != original_content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)

        except Exception as e:
            error_msg = f"Error processing {filepath}: {e}"
            print(f"❌ {error_msg}")
            self.errors_found.append(error_msg)

    def fix_all_imports(self):
        """Main function to fix all import issues"""
        print("🚀 Starting Universal Import Fixer...")
        print("=" * 50)

        # Step 1: Install missing packages
        self.install_missing_packages()
        print()

        # Step 2: Fix import statements in all Python files
        print("🔍 Scanning Python files for import issues...")

        for root, dirs, files in os.walk('.'):
            # Skip venv and cache directories
            dirs[:] = [d for d in dirs if d not in ['venv', '__pycache__', '.git', 'node_modules']]

            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    self.scan_and_fix_file(filepath)

        # Step 3: Generate/update requirements.txt
        print("\n📝 Updating requirements.txt...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "freeze"], 
                                stdout=open('requirements.txt', 'w'))
            print("✅ requirements.txt updated")
        except Exception as e:
            print(f"❌ Failed to update requirements.txt: {e}")

        # Summary
        print("\n" + "=" * 50)
        print(f"✅ Import Fixer Complete!")
        print(f"📊 Fixes applied: {self.fixes_applied}")
        if self.errors_found:
            print(f"❌ Errors found: {len(self.errors_found)}")
            for error in self.errors_found:
                print(f"   - {error}")
        else:
            print("🎉 No errors found!")

if __name__ == "__main__":
    fixer = ImportFixer()
    fixer.fix_all_imports()