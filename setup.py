#!/usr/bin/env python
"""
UPG Management System Setup Script
Automated setup for local development and testing
"""

import os
import sys
import subprocess
import django
from django.core.management import execute_from_command_line


def run_command(command, description):
    """Run a command and print status"""
    print(f"\n{'='*50}")
    print(f"STEP: {description}")
    print(f"{'='*50}")

    try:
        if isinstance(command, str):
            result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        else:
            result = subprocess.run(command, check=True, capture_output=True, text=True)

        if result.stdout:
            print(f"Output: {result.stdout}")

        print(f"✅ SUCCESS: {description}")
        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ ERROR: {description}")
        print(f"Error output: {e.stderr if e.stderr else e.stdout}")
        return False


def install_requirements():
    """Install Python requirements"""
    return run_command([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'],
                      "Installing Python requirements")


def run_migrations():
    """Run Django migrations"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'upg_system.settings')

    # Make migrations
    success1 = run_command([sys.executable, 'manage.py', 'makemigrations'],
                          "Creating database migrations")

    # Apply migrations
    success2 = run_command([sys.executable, 'manage.py', 'migrate'],
                          "Applying database migrations")

    return success1 and success2


def create_superuser():
    """Create superuser account"""
    print(f"\n{'='*50}")
    print("STEP: Creating superuser account")
    print(f"{'='*50}")

    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'upg_system.settings')
        execute_from_command_line(['manage.py', 'createsuperuser'])
        print("✅ SUCCESS: Superuser created")
        return True
    except Exception as e:
        print(f"❌ ERROR: Failed to create superuser - {e}")
        return False


def load_sample_data():
    """Load sample data"""
    return run_command([sys.executable, 'manage.py', 'loaddata', 'sample_data.json'],
                      "Loading sample data")


def collect_static():
    """Collect static files"""
    return run_command([sys.executable, 'manage.py', 'collectstatic', '--noinput'],
                      "Collecting static files")


def main():
    """Main setup function"""
    print("🚀 UPG Management System Setup")
    print("This script will set up the UPG system for local development and testing\n")

    # Check if we're in the right directory
    if not os.path.exists('manage.py'):
        print("❌ ERROR: manage.py not found. Please run this script from the project root directory.")
        sys.exit(1)

    # Step 1: Install requirements
    if not install_requirements():
        print("⚠️  WARNING: Requirements installation failed. Please install manually.")

    # Step 2: Run migrations
    if not run_migrations():
        print("❌ CRITICAL: Database migration failed. Setup cannot continue.")
        sys.exit(1)

    # Step 3: Create superuser
    print("\n📝 Now you need to create a superuser account for system administration:")
    if not create_superuser():
        print("⚠️  WARNING: Superuser creation failed. You can create one later with: python manage.py createsuperuser")

    # Step 4: Collect static files
    if not collect_static():
        print("⚠️  WARNING: Static file collection failed.")

    # Final instructions
    print(f"\n{'='*60}")
    print("🎉 UPG MANAGEMENT SYSTEM SETUP COMPLETE!")
    print(f"{'='*60}")
    print("\n📋 NEXT STEPS:")
    print("1. Start the development server:")
    print("   python manage.py runserver")
    print("\n2. Open your browser and go to:")
    print("   http://127.0.0.1:8000")
    print("\n3. Login with the superuser account you created")
    print("\n4. Access the admin panel at:")
    print("   http://127.0.0.1:8000/admin")
    print("\n5. Start adding data and testing the system!")
    print(f"\n{'='*60}")


if __name__ == '__main__':
    main()