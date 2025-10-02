# MariaDB Upgrade Guide - From 10.4.32 to 10.5+

## Current Status
- **Current Version**: MariaDB 10.4.32 (XAMPP)
- **Required Version**: MariaDB 10.5+ for Django 5.2.6
- **Location**: C:\xampp\mysql\

## ⚠️ IMPORTANT: Backup First!

Before starting any upgrade, **BACKUP YOUR DATABASES**:

```bash
# 1. Stop XAMPP services first
# 2. Create backup of your data directory
xcopy "C:\xampp\mysql\data" "C:\xampp_backup\mysql_data_backup" /E /I /H

# 3. Export your UPG database (alternative backup)
"C:\xampp\mysql\bin\mysqldump.exe" -u root --all-databases > "C:\xampp_backup\all_databases_backup.sql"
```

## Option 1: Download Latest XAMPP (Recommended)

This is the **easiest and safest** method:

### Step 1: Download Latest XAMPP
1. Go to https://www.apachefriends.org/download.html
2. Download the latest XAMPP version (usually includes MariaDB 10.6+ or 11.x)
3. Choose the installer version for Windows

### Step 2: Backup and Prepare
```bash
# Stop current XAMPP services
# Backup your data (see backup section above)
# Note your current settings in C:\xampp\mysql\bin\my.ini
```

### Step 3: Install New XAMPP
1. **Don't uninstall old XAMPP yet**
2. Install new XAMPP to a different directory (e.g., `C:\xampp_new\`)
3. Choose custom installation if you only want to update MySQL/MariaDB

### Step 4: Migrate Data
```bash
# Copy your data directory to new installation
xcopy "C:\xampp\mysql\data" "C:\xampp_new\mysql\data" /E /I /H /Y

# Or restore from SQL backup
"C:\xampp_new\mysql\bin\mysql.exe" -u root < "C:\xampp_backup\all_databases_backup.sql"
```

### Step 5: Switch XAMPP Installations
1. Stop old XAMPP services
2. Rename old XAMPP: `C:\xampp` → `C:\xampp_old`
3. Rename new XAMPP: `C:\xampp_new` → `C:\xampp`
4. Start new XAMPP services

## Option 2: Manual MariaDB Upgrade (Advanced)

### Step 1: Download MariaDB
1. Go to https://mariadb.org/download/
2. Download MariaDB 10.11 LTS (stable) or 11.x for Windows
3. Choose the ZIP package (not MSI installer)

### Step 2: Stop XAMPP and Backup
```bash
# Stop MySQL service in XAMPP Control Panel
# Backup data directory (see backup section)
```

### Step 3: Replace MariaDB Binaries
```bash
# Rename current mysql directory
move "C:\xampp\mysql" "C:\xampp\mysql_old"

# Extract new MariaDB to C:\xampp\mysql
# Copy configuration files from old installation
copy "C:\xampp\mysql_old\bin\my.ini" "C:\xampp\mysql\bin\"
copy "C:\xampp\mysql_old\data" "C:\xampp\mysql\data" /E
```

### Step 4: Upgrade Database
```bash
# Start MySQL service
# Run mysql_upgrade utility
"C:\xampp\mysql\bin\mysql_upgrade.exe" -u root
```

## Option 3: Standalone MySQL 8.0 Installation

If you prefer MySQL over MariaDB:

### Step 1: Download MySQL
1. Go to https://dev.mysql.com/downloads/mysql/
2. Download MySQL 8.0 Community Server
3. Choose ZIP Archive (not installer)

### Step 2: Install Alongside XAMPP
```bash
# Extract to C:\mysql80\
# Configure to use port 3307 (to avoid conflict with XAMPP)
# Update Django settings to use port 3307
```

### Step 3: Update Django Settings
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'upg_management_system',
        'USER': 'root',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '3307',  # Different port
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
        },
    }
}
```

## Recommended Approach

For your situation, I recommend **Option 1** (Latest XAMPP) because:
- ✅ Easiest and safest
- ✅ Ensures all components are compatible
- ✅ Includes latest PHP, Apache updates
- ✅ Minimal configuration needed
- ✅ Easy rollback if issues occur

## Quick Steps Summary (Option 1)

1. **Backup your database**:
   ```bash
   "C:\xampp\mysql\bin\mysqldump.exe" -u root --all-databases > "C:\xampp_backup\all_databases.sql"
   ```

2. **Download latest XAMPP** from https://www.apachefriends.org/

3. **Install to new directory** (e.g., `C:\xampp_new`)

4. **Stop old XAMPP, start new XAMPP**

5. **Import your data**:
   ```bash
   "C:\xampp_new\mysql\bin\mysql.exe" -u root < "C:\xampp_backup\all_databases.sql"
   ```

6. **Update Django settings** (uncomment MySQL configuration)

7. **Test the migration**:
   ```bash
   python manage.py migrate
   ```

## After Upgrade: Activate MySQL in Django

Once you have MariaDB 10.5+, activate MySQL in your Django settings:

```python
# In upg_system/settings.py
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
        'PASSWORD': '',  # XAMPP default
        'HOST': 'localhost',
        'PORT': '3306',
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
        },
    }
}
```

## Verification Commands

After upgrade, verify the version:

```bash
# Check MariaDB version
"C:\xampp\mysql\bin\mysql.exe" --version

# Test Django connection
cd "C:\Users\Derick Joseph\OneDrive\CHASP\UPG\UPG_System"
python manage.py check
python manage.py migrate
```

## Rollback Plan

If anything goes wrong:

1. Stop new XAMPP
2. Rename directories back: `C:\xampp` → `C:\xampp_new`, `C:\xampp_old` → `C:\xampp`
3. Start old XAMPP
4. Restore from backup if needed

## Support

- MariaDB Documentation: https://mariadb.com/kb/en/upgrading/
- XAMPP Forums: https://community.apachefriends.org/
- Django Database docs: https://docs.djangoproject.com/en/5.2/ref/databases/

---

**Ready to proceed?** I recommend starting with the backup step, then downloading the latest XAMPP.