#!/usr/bin/env python3
"""
Fix relative imports in daily_run modules for Railway deployment
"""

import os
import re

def fix_relative_imports_in_file(file_path):
    """Fix relative imports in a single file"""
    print(f"Fixing: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Find all relative imports
    relative_import_pattern = r'^from \.([a-zA-Z_][a-zA-Z0-9_]*) import (.+)$'
    
    lines = content.split('\n')
    new_lines = []
    
    for line in lines:
        # Check if it's a relative import
        match = re.match(relative_import_pattern, line)
        if match:
            module_name = match.group(1)
            imports = match.group(2)
            
            # Create try/except block for relative/absolute import
            new_lines.append('try:')
            new_lines.append(f'    from .{module_name} import {imports}')
            new_lines.append('except ImportError:')
            new_lines.append(f'    from {module_name} import {imports}')
        else:
            new_lines.append(line)
    
    new_content = '\n'.join(new_lines)
    
    # Only write if content changed
    if new_content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"  ✅ Fixed relative imports in {file_path}")
        return True
    else:
        print(f"  ℹ️ No changes needed in {file_path}")
        return False

def main():
    """Fix relative imports in all Python files in daily_run"""
    print("🔧 FIXING RELATIVE IMPORTS FOR RAILWAY DEPLOYMENT")
    print("=" * 60)
    
    daily_run_dir = 'daily_run'
    fixed_count = 0
    
    # Walk through all Python files in daily_run
    for root, dirs, files in os.walk(daily_run_dir):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                if fix_relative_imports_in_file(file_path):
                    fixed_count += 1
    
    print(f"\n📊 SUMMARY: Fixed {fixed_count} files")
    print("🚀 Ready for Railway deployment!")

if __name__ == "__main__":
    main()
