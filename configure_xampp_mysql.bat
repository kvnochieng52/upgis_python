@echo off
echo ================================================
echo    Configure UPG System for XAMPP MySQL
echo ================================================
echo.

echo Checking if XAMPP MySQL is running...
echo.

REM Check if MySQL port 3306 is active
netstat -an | find "3306" | find "LISTENING" >nul
if %errorLevel% NEQ 0 (
    echo ❌ MySQL is not running on port 3306
    echo.
    echo Please:
    echo 1. Open XAMPP Control Panel
    echo 2. Click "Start" next to MySQL
    echo 3. Wait for it to show "Running" status
    echo 4. Run this script again
    echo.
    pause
    exit /b 1
)

echo ✅ MySQL is running on port 3306!
echo.

echo Testing MySQL connection...
python -c "import mysql.connector; mysql.connector.connect(host='localhost', user='root', password='', port=3306); print('✅ MySQL connection successful!')"

if %errorLevel% NEQ 0 (
    echo ❌ Could not connect to MySQL
    echo.
    echo Please check:
    echo 1. XAMPP MySQL is running
    echo 2. Port 3306 is not blocked
    echo 3. mysqlclient is installed: pip install mysqlclient
    echo.
    pause
    exit /b 1
)

echo.
echo Creating UPG database...
echo.

python -c "
import mysql.connector
try:
    conn = mysql.connector.connect(host='localhost', user='root', password='', port=3306)
    cursor = conn.cursor()
    cursor.execute('CREATE DATABASE IF NOT EXISTS upg_management_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci')
    cursor.execute('SHOW DATABASES LIKE \"upg_management_system\"')
    result = cursor.fetchone()
    if result:
        print('✅ Database upg_management_system created/exists')
    else:
        print('❌ Failed to create database')
        exit(1)
    conn.close()
except Exception as e:
    print(f'❌ Error: {e}')
    exit(1)
"

if %errorLevel% NEQ 0 (
    echo Database creation failed
    pause
    exit /b 1
)

echo.
echo Updating Django settings...
echo.

REM Backup current settings
if exist upg_system\settings.py (
    copy upg_system\settings.py upg_system\settings_backup_%date:~-4,4%%date:~-10,2%%date:~-7,2%.py >nul
    echo ✅ Settings backed up
)

REM Update settings.py for XAMPP MySQL
python -c "
import re

# Read current settings
with open('upg_system/settings.py', 'r') as f:
    content = f.read()

# Replace database configuration
mysql_config = '''# Database - XAMPP MySQL Configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'upg_management_system',
        'USER': 'root',
        'PASSWORD': '',  # XAMPP default (no password)
        'HOST': 'localhost',
        'PORT': '3306',
        'OPTIONS': {
            'init_command': \"SET sql_mode='STRICT_TRANS_TABLES'\",
        },
    }
}'''

# Replace existing database configuration
content = re.sub(r'# Database.*?^}', mysql_config, content, flags=re.MULTILINE | re.DOTALL)

# Write updated settings
with open('upg_system/settings.py', 'w') as f:
    f.write(content)

print('✅ Django settings updated for XAMPP MySQL')
"

if %errorLevel% NEQ 0 (
    echo ❌ Failed to update settings
    pause
    exit /b 1
)

echo.
echo Running database migrations...
echo.

python manage.py migrate

if %errorLevel% NEQ 0 (
    echo ❌ Migration failed
    echo Restoring previous settings...
    if exist upg_system\settings_backup_*.py (
        for /f %%i in ('dir /b upg_system\settings_backup_*.py') do copy "upg_system\%%i" upg_system\settings.py >nul
    )
    pause
    exit /b 1
)

echo.
echo ================================================
echo ✅ XAMPP MySQL Setup Complete!
echo ================================================
echo.
echo ✅ XAMPP MySQL is running
echo ✅ UPG database created
echo ✅ Django configured for MySQL
echo ✅ Database migrations applied successfully
echo.
echo Your UPG Management System is now using XAMPP MySQL!
echo.
echo 🚀 To start your system:
echo   python manage.py runserver
echo.
echo 🌐 Access your system:
echo   - UPG System: http://127.0.0.1:8000
echo   - Admin Panel: http://127.0.0.1:8000/admin
echo   - phpMyAdmin: http://127.0.0.1/phpmyadmin
echo.
echo 📁 Backup files created:
echo   - settings_backup_*.py (previous configuration)
echo.
echo 💡 XAMPP Control Panel:
echo   - Start/Stop MySQL anytime
echo   - Access phpMyAdmin for database management
echo   - Monitor MySQL status
echo.
pause