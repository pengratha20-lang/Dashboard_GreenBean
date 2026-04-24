"""
Frontend Application Startup Script
Runs on port 5000
"""

import os
import subprocess
import sys

# Set environment variable
os.environ['APP_MODE'] = 'frontend'

print("\n" + "="*60)
print("Starting GreenBean Frontend Application")
print("="*60)
print("✓ Port: 5000")
print("✓ URL: http://localhost:5000")
print("✓ Mode: FRONTEND (Customer Site)")
print("="*60 + "\n")

# Run the unified app
subprocess.run([sys.executable, 'app.py'])
