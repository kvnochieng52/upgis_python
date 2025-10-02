@echo off
echo ================================================
echo    XAMPP MySQL Installation (No Admin Required)
echo ================================================
echo.

echo This method installs MySQL via XAMPP without requiring Administrator rights
echo.

echo Step 1: Download XAMPP
echo =====================
echo Please follow these steps:
echo.
echo 1. Open your web browser
echo 2. Go to: https://www.apachefriends.org/
echo 3. Click "Download" for Windows
echo 4. Download the latest XAMPP version
echo 5. Save it to your Downloads folder
echo.

pause

echo Step 2: Install XAMPP
echo =====================
echo.
echo 1. Run the XAMPP installer (from your Downloads)
echo 2. If Windows asks about firewall, click "Allow access"
echo 3. Choose installation directory: C:\xampp (default)
echo 4. Select these components:
echo    ✅ Apache
echo    ✅ MySQL
echo    ✅ PHP
echo    ✅ phpMyAdmin
echo    ❌ Uncheck other components
echo 5. Complete the installation
echo.

pause

echo Step 3: Start MySQL
echo ===================
echo.
echo 1. Open XAMPP Control Panel (from Start menu or desktop)
echo 2. Click "Start" button next to MySQL
echo 3. MySQL status should show "Running" in green
echo.

pause

echo Step 4: Create Database
echo =======================
echo.
echo 1. In XAMPP Control Panel, click "Admin" next to MySQL
echo 2. This opens phpMyAdmin in your browser
echo 3. Click "New" on the left sidebar
echo 4. Database name: upg_management_system
echo 5. Collation: utf8mb4_unicode_ci
echo 6. Click "Create"
echo.

pause

echo Step 5: Configure UPG System
echo ============================
echo.
echo Now I'll configure your UPG system to use MySQL...
echo.

REM Create XAMPP MySQL configuration
echo Updating Django settings for XAMPP MySQL...

REM Backup current settings
copy upg_system\settings.py upg_system\settings_sqlite_backup.py >nul

REM Create new settings content
(
echo # Database - XAMPP MySQL Configuration
echo DATABASES = {
echo     'default': {
echo         'ENGINE': 'django.db.backends.mysql',
echo         'NAME': 'upg_management_system',
echo         'USER': 'root',
echo         'PASSWORD': '',  # XAMPP MySQL has no password by default
echo         'HOST': 'localhost',
echo         'PORT': '3306',
echo         'OPTIONS': {
echo             'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
echo         },
echo     }
echo }
) > mysql_config.txt

echo.
echo ================================================
echo Next Steps:
echo ================================================
echo.
echo 1. Complete XAMPP installation and start MySQL
echo 2. Create the database in phpMyAdmin
echo 3. Run: configure_xampp_mysql.bat
echo 4. Your UPG system will be ready with MySQL!
echo.
echo XAMPP Benefits:
echo ✅ No Administrator privileges needed
echo ✅ Easy to start/stop MySQL
echo ✅ Includes phpMyAdmin for database management
echo ✅ Perfect for development
echo.
pause