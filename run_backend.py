"""
Backend Application Startup Script
Runs on port 5001
"""

import os
import subprocess
import sys

# Set environment variable
os.environ['APP_MODE'] = 'backend'

print("\n" + "="*60)
print("Starting GreenBean Backend Application")
print("="*60)
print("✓ Port: 5001")
print("✓ URL: http://localhost:5001")
print("✓ Mode: BACKEND (Admin Dashboard)")
print("="*60 + "\n")

# Run the unified app
subprocess.run([sys.executable, 'app.py'])
