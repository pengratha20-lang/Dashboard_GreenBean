"""
Start the Application (Both Frontend and Backend on Port 5000)
Admin Dashboard: http://127.0.0.1:5000/admin/login
Customer Site: http://127.0.0.1:5000
"""

import subprocess
import sys

print("\n" + "="*60)
print("Starting GreenBean Application")
print("="*60)
print("✓ Customer Site: http://127.0.0.1:5000")
print("✓ Admin Panel:   http://127.0.0.1:5000/admin/login")
print("="*60 + "\n")

# Run the unified app
subprocess.run([sys.executable, 'app.py'])
