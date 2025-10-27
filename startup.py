#!/usr/bin/env python
import os
import sys
import subprocess
import shutil
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Budget_Tracker.settings')
django.setup()

from django.core.management import call_command
from Tracker.models import TransactionType

def main():
    print("Starting Budget Tracker setup...")

    # Run database migrations
    print("Running database migrations...")
    call_command('migrate', verbosity=0)

    # Check if setup_transaction_types has been run
    if TransactionType.objects.count() == 0:
        print("Transaction types not set up. Running setup...")
        result = subprocess.run([sys.executable, 'setup_transaction_types.py'])
        if result.returncode != 0:
            print("Failed to run setup script.")
            sys.exit(1)
    else:
        print("Transaction types already set up. Skipping setup.")

    # Install Python requirements
    print("Installing Python requirements...")
    result = subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
    if result.returncode != 0:
        print("Failed to install Python requirements.")
        sys.exit(1)

    # Check and install Vue dependencies
    vue_dir = 'tracker_vue'
    npm_cmd = 'npm.cmd' if os.name == 'nt' else 'npm'
    if not os.path.exists(os.path.join(vue_dir, 'node_modules')):
        print("Installing Vue dependencies...")
        os.chdir(vue_dir)
        try:
            result = subprocess.run([npm_cmd, 'install'])
        except FileNotFoundError:
            print("npm not found. Please install Node.js and npm.")
            os.chdir('..')
            sys.exit(1)
        os.chdir('..')
        if result.returncode != 0:
            print("Failed to install Vue dependencies.")
            sys.exit(1)
    else:
        print("Vue dependencies already installed.")

    # Start Django server
    print("Starting Django server...")
    django_proc = subprocess.Popen([sys.executable, 'manage.py', 'runserver'])

    # Start Vue server
    print("Starting Vue development server...")
    os.chdir(vue_dir)
    try:
        vue_proc = subprocess.Popen([npm_cmd, 'run', 'serve'])
    except FileNotFoundError:
        print("npm not found. Please install Node.js and npm.")
        sys.exit(1)

    print("Setup complete. Servers are starting in the background.")

if __name__ == '__main__':
    main()
