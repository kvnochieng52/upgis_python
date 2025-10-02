@echo off
echo ================================================
echo    UPG MANAGEMENT INFORMATION SYSTEM
echo    Starting Local Development Server
echo ================================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from python.org
    pause
    exit /b 1
)

:: Check if requirements are installed
echo Checking system requirements...
pip show Django >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing Python requirements...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo ERROR: Failed to install requirements
        pause
        exit /b 1
    )
)

:: Check if database exists
if not exist db.sqlite3 (
    echo Setting up database for first time...
    echo Creating database migrations...
    python manage.py makemigrations

    echo Applying database migrations...
    python manage.py migrate

    echo.
    echo ==================================================
    echo DATABASE SETUP COMPLETE
    echo You need to create an admin user account
    echo ==================================================
    python manage.py createsuperuser
)

:: Start the development server
echo.
echo ================================================
echo Starting UPG Management System...
echo ================================================
echo.
echo System will be available at: http://127.0.0.1:8000
echo Admin panel available at: http://127.0.0.1:8000/admin
echo.
echo Press Ctrl+C to stop the server
echo ================================================

python manage.py runserver

pause