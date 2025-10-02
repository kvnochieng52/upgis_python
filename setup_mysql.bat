@echo off
echo ================================================
echo    UPG SYSTEM - MYSQL SETUP
echo ================================================
echo.

echo This script will help you set up MySQL for the UPG System.
echo.
echo PREREQUISITES:
echo 1. MySQL Server must be installed and running
echo 2. MySQL root user should be accessible
echo 3. Python MySQL client library will be installed
echo.
pause

echo Installing MySQL Python client...
pip install mysqlclient

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to install mysqlclient
    echo.
    echo If you encounter errors, try one of these solutions:
    echo 1. Install Visual Studio Build Tools
    echo 2. Or download mysqlclient wheel from: https://www.lfd.uci.edu/~gohlke/pythonlibs/#mysqlclient
    echo 3. Or install MySQL Connector/Python instead: pip install mysql-connector-python
    echo.
    pause
    exit /b 1
)

echo.
echo Creating MySQL database...
echo Please enter your MySQL root password when prompted.

mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS upg_management_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to create database
    echo Please ensure MySQL is running and you have the correct password
    echo.
    pause
    exit /b 1
)

echo.
echo Database created successfully!
echo.
echo Next steps:
echo 1. Update the MySQL password in upg_system/settings.py
echo 2. Run: python manage.py makemigrations
echo 3. Run: python manage.py migrate
echo 4. Run: python manage.py createsuperuser
echo 5. Run: python manage.py runserver
echo.
echo ================================================
pause