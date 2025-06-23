#!/usr/bin/env python3
"""
Fix Unicode logging issues in integrated_daily_runner_v2.py
"""

import re

def fix_unicode_logging():
    """Replace Unicode emoji characters with text equivalents"""
    
    # Read the file
    with open('daily_run/integrated_daily_runner_v2.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace Unicode characters with text equivalents
    replacements = {
        '✅': 'SUCCESS:',
        '❌': 'FAILED:',
        '⚠️': 'WARNING:',
        '🔧': 'CONFIG:',
        '📊': 'DATA:',
        '📈': 'CHART:',
        '💰': 'FUNDAMENTAL:',
        '🚀': 'START:',
        '🔍': 'AUDIT:'
    }
    
    for unicode_char, text_replacement in replacements.items():
        content = content.replace(unicode_char, text_replacement)
    
    # Write the fixed content back
    with open('daily_run/integrated_daily_runner_v2.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Fixed Unicode logging issues in integrated_daily_runner_v2.py")

if __name__ == "__main__":
    fix_unicode_logging() 