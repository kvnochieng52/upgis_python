@echo off
echo ================================================
echo    AUTO MySQL Server Installation
echo ================================================
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% NEQ 0 (
    echo ERROR: This script must be run as Administrator
    echo Right-click this file and select "Run as administrator"
    pause
    exit /b 1
)

echo Downloading MySQL Installer...
echo.

REM Create temp directory
if not exist "%TEMP%\mysql_setup" mkdir "%TEMP%\mysql_setup"
cd /d "%TEMP%\mysql_setup"

REM Download MySQL Installer using PowerShell
powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://dev.mysql.com/get/Downloads/MySQLInstaller/mysql-installer-community-8.0.39.0.msi' -OutFile 'mysql-installer.msi'}"

if not exist "mysql-installer.msi" (
    echo ERROR: Failed to download MySQL installer
    echo Please download manually from: https://dev.mysql.com/downloads/installer/
    pause
    exit /b 1
)

echo.
echo MySQL Installer downloaded successfully!
echo.
echo Starting MySQL installation...
echo.
echo IMPORTANT INSTALLATION NOTES:
echo ==============================
echo 1. When installer opens, choose "Server only" or "Developer Default"
echo 2. Set root password as: Yimbo001$
echo 3. Choose "Use Strong Password Encryption for Authentication"
echo 4. Configure MySQL Server as Windows Service (default)
echo 5. Start the service after configuration
echo.

pause

REM Start MySQL installer
msiexec /i mysql-installer.msi /quiet

if %errorLevel% NEQ 0 (
    echo Installation may have issues. Starting manual installation...
    start mysql-installer.msi
)

echo.
echo ================================================
echo Installation started!
echo ================================================
echo.
echo After MySQL installation completes:
echo 1. MySQL Service should be running automatically
echo 2. Run: setup_upg_mysql.bat to configure the database
echo 3. The UPG system will be ready to use MySQL
echo.
pause