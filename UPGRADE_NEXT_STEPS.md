# ✅ Step 1 Complete: Database Backup Created!

Your databases have been successfully backed up to:
**`C:\xampp_backup\all_databases_backup.sql`**

## Next Steps to Upgrade MariaDB

### Option 1: Download Latest XAMPP (Recommended)

**Download Link**: https://www.apachefriends.org/download.html

**What to download:**
- XAMPP for Windows (latest version)
- Current latest: XAMPP 8.2.12 (includes MariaDB 10.11.5)
- File size: ~150MB

### Step-by-Step Instructions:

#### 1. Download and Install New XAMPP
```
1. Go to: https://www.apachefriends.org/download.html
2. Download "XAMPP for Windows" (latest version)
3. Run the installer
4. IMPORTANT: Install to "C:\xampp_new" (different directory)
5. Choose components: Apache, MySQL, PHP, phpMyAdmin
```

#### 2. Stop Current XAMPP
```
1. Open XAMPP Control Panel
2. Stop Apache and MySQL services
3. Close XAMPP Control Panel
```

#### 3. Test New Installation
```
1. Navigate to C:\xampp_new\
2. Run xampp-control.exe
3. Start MySQL service
4. Verify new version:
   "C:\xampp_new\mysql\bin\mysql.exe" --version
   (Should show MariaDB 10.11+ or similar)
```

#### 4. Restore Your Database
```bash
# Navigate to new XAMPP directory
cd "C:\xampp_new\mysql\bin"

# Import your backup
mysql.exe -u root < "C:\xampp_backup\all_databases_backup.sql"
```

#### 5. Switch to New Installation
```
1. Stop new XAMPP services
2. Rename folders:
   - C:\xampp → C:\xampp_old
   - C:\xampp_new → C:\xampp
3. Start XAMPP services
```

#### 6. Update Django Settings
```python
# Edit: C:\Users\Derick Joseph\OneDrive\CHASP\UPG\UPG_System\upg_system\settings.py

# Comment out SQLite:
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }

# Uncomment MySQL:
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'upg_management_system',
        'USER': 'root',
        'PASSWORD': '',
        'HOST': 'localhost',
        'PORT': '3306',
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
        },
    }
}
```

#### 7. Test Django with New MariaDB
```bash
cd "C:\Users\Derick Joseph\OneDrive\CHASP\UPG\UPG_System"

# Test connection
python manage.py check

# Create MySQL database
"C:\xampp\mysql\bin\mysql.exe" -u root -e "CREATE DATABASE IF NOT EXISTS upg_management_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# Run migrations
python manage.py migrate

# Test server
python manage.py runserver
```

### Alternative: Quick Method Using Chocolatey (if available)

If you have Chocolatey package manager:
```bash
# Install latest XAMPP via Chocolatey
choco install xampp-81 --force

# This automatically handles the upgrade
```

### Verification Commands

After upgrade, run these to confirm success:

```bash
# Check MariaDB version (should be 10.5+)
"C:\xampp\mysql\bin\mysql.exe" --version

# Check Django compatibility
cd "C:\Users\Derick Joseph\OneDrive\CHASP\UPG\UPG_System"
python manage.py check

# Test database connection
python manage.py shell -c "from django.db import connection; print('✅ Database connected:', connection.vendor)"
```

## Download Links Summary

- **XAMPP Official**: https://www.apachefriends.org/download.html
- **MariaDB Standalone**: https://mariadb.org/download/ (if you prefer manual upgrade)
- **MySQL 8.0 Alternative**: https://dev.mysql.com/downloads/mysql/

## Expected Results

After successful upgrade:
- ✅ MariaDB 10.11+ (or similar recent version)
- ✅ Django 5.2.6 compatibility resolved
- ✅ UPG system running on MySQL instead of SQLite
- ✅ All existing data preserved
- ✅ Better performance for larger datasets

## Rollback Plan

If anything goes wrong:
1. Stop new XAMPP: Close xampp-control.exe
2. Restore old installation: Rename `C:\xampp_old` back to `C:\xampp`
3. Revert Django settings to SQLite
4. Your SQLite database (`db.sqlite3`) is unchanged as a backup

## Need Help?

If you encounter any issues during the upgrade:
1. Check the error messages carefully
2. Verify port 3306 is not in use by other services
3. Ensure Windows Firewall allows MySQL connections
4. Try running XAMPP as Administrator

**Ready to proceed?** Start by downloading the latest XAMPP from the official website!