@echo off
echo ================================================
echo    UPG System MySQL Configuration
echo ================================================
echo.

REM Check if MySQL service is running
sc query mysql80 | find "RUNNING" >nul
if %errorLevel% NEQ 0 (
    echo Starting MySQL service...
    net start mysql80
    if %errorLevel% NEQ 0 (
        echo ERROR: Could not start MySQL service
        echo Please check if MySQL is installed correctly
        pause
        exit /b 1
    )
)

echo MySQL service is running!
echo.

echo Creating UPG database...
echo When prompted, enter MySQL root password: Yimbo001$
echo.

REM Try different possible MySQL paths
set MYSQL_PATH=""
if exist "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" set MYSQL_PATH="C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe"
if exist "C:\Program Files\MySQL\MySQL Server 8.4\bin\mysql.exe" set MYSQL_PATH="C:\Program Files\MySQL\MySQL Server 8.4\bin\mysql.exe"
if exist "C:\Program Files\MySQL\MySQL Server 9.0\bin\mysql.exe" set MYSQL_PATH="C:\Program Files\MySQL\MySQL Server 9.0\bin\mysql.exe"

if %MYSQL_PATH%=="" (
    echo ERROR: Could not find MySQL executable
    echo Please add MySQL to your PATH or check installation
    pause
    exit /b 1
)

echo Using MySQL at: %MYSQL_PATH%

%MYSQL_PATH% -u root -p -e "CREATE DATABASE IF NOT EXISTS upg_management_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci; SHOW DATABASES;"

if %errorLevel% NEQ 0 (
    echo ERROR: Failed to create database
    echo Please check your MySQL root password
    pause
    exit /b 1
)

echo.
echo ✅ Database created successfully!
echo.

echo Updating Django configuration...
echo.

REM Backup current settings
copy upg_system\settings.py upg_system\settings_sqlite_backup.py >nul

REM Update settings to use MySQL
powershell -Command "(Get-Content upg_system\settings.py) -replace '# For now using SQLite.*', '# MySQL Configuration - Active' -replace 'DATABASES = \{[^}]+\}', 'DATABASES = { ''default'': { ''ENGINE'': ''django.db.backends.mysql'', ''NAME'': ''upg_management_system'', ''USER'': ''root'', ''PASSWORD'': ''Yimbo001$'', ''HOST'': ''localhost'', ''PORT'': ''3306'', ''OPTIONS'': { ''init_command'': ''SET sql_mode=''''STRICT_TRANS_TABLES'''''', }, } }' | Set-Content upg_system\settings_mysql.py"

REM Replace settings file
move upg_system\settings_mysql.py upg_system\settings.py >nul

echo Django configuration updated!
echo.

echo Running database migrations...
echo.
python manage.py migrate

if %errorLevel% NEQ 0 (
    echo ERROR: Migration failed
    echo Restoring SQLite configuration...
    move upg_system\settings_sqlite_backup.py upg_system\settings.py >nul
    pause
    exit /b 1
)

echo.
echo ================================================
echo MySQL Setup Complete! ✅
echo ================================================
echo.
echo ✅ MySQL Server installed and running
echo ✅ UPG database created
echo ✅ Django configured for MySQL
echo ✅ Database migrations applied
echo.
echo Your UPG Management System is now using MySQL!
echo.
echo To start the system:
echo   python manage.py runserver
echo.
echo Access at: http://127.0.0.1:8000
echo Admin at: http://127.0.0.1:8000/admin
echo.
echo Backup files created:
echo   - settings_sqlite_backup.py (SQLite configuration backup)
echo.
pause