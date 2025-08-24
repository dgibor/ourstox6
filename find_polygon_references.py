#!/usr/bin/env python3
"""
Simple script to find all Polygon.io references in the codebase
"""
import os
import re

def find_polygon_references():
    """Find all files containing Polygon.io references"""
    print("🔍 Searching for Polygon.io references...")
    print("=" * 50)
    
    polygon_files = []
    
    # Search in daily_run directory
    for root, dirs, files in os.walk('daily_run'):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if 'polygon' in content.lower():
                            polygon_files.append(file_path)
                            print(f"📁 {file_path}")
                except Exception as e:
                    print(f"❌ Error reading {file_path}: {e}")
    
    print(f"\n📊 Found {len(polygon_files)} files with Polygon.io references")
    
    # Now check each file for specific usage patterns
    for file_path in polygon_files:
        print(f"\n🔍 Checking {file_path}:")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
                
                for i, line in enumerate(lines, 1):
                    if 'polygon' in line.lower():
                        print(f"  Line {i}: {line.strip()}")
                        
        except Exception as e:
            print(f"  ❌ Error reading file: {e}")

if __name__ == "__main__":
    find_polygon_references()
