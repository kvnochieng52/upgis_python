@echo off
echo ================================================
echo    MySQL Server Installation for UPG System
echo ================================================
echo.
echo MySQL Server is not currently installed on your system.
echo.
echo OPTION 1: Download and Install MySQL Server
echo ------------------------------------------
echo 1. Visit: https://dev.mysql.com/downloads/installer/
echo 2. Download "MySQL Installer for Windows" (web installer)
echo 3. Run the installer and select "Server only" or "Developer Default"
echo 4. During setup:
echo    - Set root password as: Yimbo001$
echo    - Choose "Use Strong Password Encryption"
echo    - Start MySQL as Windows Service
echo 5. After installation, run this script again
echo.
echo OPTION 2: Use XAMPP (Quick Setup)
echo ---------------------------------
echo 1. Visit: https://www.apachefriends.org/
echo 2. Download XAMPP for Windows
echo 3. Install XAMPP (includes MySQL)
echo 4. Start MySQL from XAMPP Control Panel
echo 5. Access MySQL via phpMyAdmin or command line
echo.
echo OPTION 3: Continue with SQLite (Current Setup)
echo ----------------------------------------------
echo Your system is already working with SQLite database.
echo This is sufficient for development and testing.
echo You can switch to MySQL later when needed.
echo.
pause