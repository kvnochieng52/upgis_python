# 🔄 LIVE MariaDB Upgrade Checklist

## Current Status:
- ✅ Database backup created: `C:\xampp_backup\all_databases_backup.sql`
- ✅ MySQL client installed: `mysqlclient 2.2.7`
- ✅ Current MariaDB running on port 3306
- ✅ Current version: 10.4.32

## Step-by-Step Upgrade Process:

### Phase 1: Download & Prepare ⏳

**☐ 1. Download Latest XAMPP**
- Go to: https://www.apachefriends.org/download.html
- Download: "XAMPP for Windows" (latest version)
- Expected: XAMPP 8.2.x with MariaDB 10.11+

**☐ 2. Verify Download**
- File size should be ~150-200MB
- Filename: `xampp-windows-x64-8.2.x-installer.exe`

### Phase 2: Installation 🚀

**☐ 3. Run XAMPP Installer**
```
- Right-click installer → "Run as Administrator"
- Choose installation directory: C:\xampp_new
- Select components: ✅ Apache ✅ MySQL ✅ PHP ✅ phpMyAdmin
- Uncheck: FileZilla, Mercury, Tomcat (unless needed)
```

**☐ 4. Complete Installation**
- Wait for installation to finish
- Don't start services yet
- Note the installation path

### Phase 3: Service Management 🔄

**☐ 5. Stop Current XAMPP**
```
Method 1: XAMPP Control Panel
- Open C:\xampp\xampp-control.exe
- Click "Stop" for Apache and MySQL
- Close Control Panel

Method 2: Command Line (if needed)
- net stop mysql
- net stop apache2.4
```

**☐ 6. Test New Installation**
```
- Navigate to C:\xampp_new\
- Run xampp-control.exe
- Start MySQL service only
- Check version: "C:\xampp_new\mysql\bin\mysql.exe" --version
- Should show MariaDB 10.11+ or similar
```

### Phase 4: Data Migration 📊

**☐ 7. Create UPG Database in New MariaDB**
```bash
"C:\xampp_new\mysql\bin\mysql.exe" -u root -e "CREATE DATABASE IF NOT EXISTS upg_management_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

**☐ 8. Import Your Data**
```bash
"C:\xampp_new\mysql\bin\mysql.exe" -u root < "C:\xampp_backup\all_databases_backup.sql"
```

**☐ 9. Verify Data Import**
```bash
"C:\xampp_new\mysql\bin\mysql.exe" -u root -e "USE upg_management_system; SHOW TABLES; SELECT COUNT(*) FROM upg_households;"
```

### Phase 5: Switch Installations 🔄

**☐ 10. Stop New XAMPP Services**
- Stop MySQL in C:\xampp_new\xampp-control.exe

**☐ 11. Backup & Rename Directories**
```bash
# Rename old XAMPP as backup
move "C:\xampp" "C:\xampp_old"

# Move new XAMPP to main location
move "C:\xampp_new" "C:\xampp"
```

**☐ 12. Start New XAMPP**
- Open C:\xampp\xampp-control.exe
- Start Apache and MySQL
- Verify both services start successfully

### Phase 6: Django Configuration 🐍

**☐ 13. Update Django Settings**
```python
# Edit: upg_system/settings.py
# Comment out SQLite configuration:
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }

# Uncomment MySQL configuration:
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

### Phase 7: Testing & Verification ✅

**☐ 14. Test Django Connection**
```bash
cd "C:\Users\Derick Joseph\OneDrive\CHASP\UPG\UPG_System"
python manage.py check
```

**☐ 15. Run Database Migrations**
```bash
python manage.py migrate
```

**☐ 16. Test Application**
```bash
python manage.py runserver
# Visit: http://localhost:8000
# Test login, grants, training modules
```

**☐ 17. Verify Data Integrity**
- Login to your UPG system
- Check that all households, grants, trainings are present
- Test creating new records
- Test reports generation

### Phase 8: Cleanup 🧹

**☐ 18. Final Verification**
```bash
# Check MariaDB version
"C:\xampp\mysql\bin\mysql.exe" --version

# Check Django database
python manage.py shell -c "from django.db import connection; print('Database:', connection.vendor, connection.mysql_version)"
```

**☐ 19. Optional Cleanup**
- If everything works: Delete C:\xampp_old (saves ~500MB space)
- Keep backup: C:\xampp_backup\ (important!)

---

## 🚨 Emergency Rollback Plan

If anything goes wrong:

**☐ Rollback Steps:**
1. Stop new XAMPP services
2. `move "C:\xampp" "C:\xampp_failed"`
3. `move "C:\xampp_old" "C:\xampp"`
4. Start old XAMPP services
5. Revert Django settings to SQLite
6. `python manage.py runserver` (should work with SQLite)

---

## ✅ Success Criteria

You'll know the upgrade succeeded when:
- ✅ MariaDB version shows 10.11+ (not 10.4.32)
- ✅ Django `manage.py check` passes
- ✅ Django `manage.py migrate` completes without errors
- ✅ UPG system loads at http://localhost:8000
- ✅ All your data is visible and functional
- ✅ No "MariaDB 10.5 or later is required" errors

---

**Ready to start?** Begin with Phase 1: Download the latest XAMPP!