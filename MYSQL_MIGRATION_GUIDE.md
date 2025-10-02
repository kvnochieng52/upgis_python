# MySQL Migration Guide for UPG System

## Current Status
The UPG System has been configured for MySQL/MariaDB but is temporarily running on SQLite due to a version compatibility issue.

## Issue
- **Current XAMPP MariaDB Version**: 10.4.32
- **Django 5.2.6 Requirement**: MariaDB 10.5+ or MySQL 8.0+
- **Error**: "MariaDB 10.5 or later is required (found 10.4.32)"

## Configuration Ready
The MySQL configuration is ready and stored in `upg_system/settings.py`:

```python
# MySQL Configuration (Ready for activation when compatible version available)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'upg_management_system',
        'USER': 'root',
        'PASSWORD': '',  # XAMPP default (no password)
        'HOST': 'localhost',
        'PORT': '3306',
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
        },
        'TEST': {
            'CHARSET': 'utf8mb4',
            'COLLATION': 'utf8mb4_unicode_ci',
        },
    }
}
```

## How to Complete MySQL Migration

### Option 1: Upgrade XAMPP (Recommended)
1. Download the latest XAMPP version with MariaDB 10.5+ or MySQL 8.0+
2. Backup your current database if it contains data
3. Install the new XAMPP version
4. Restore your database data if needed

### Option 2: Install Standalone MySQL 8.0+
1. Download and install MySQL 8.0+ from mysql.com
2. Configure it to run on port 3306 (or update settings accordingly)
3. Create user 'root' with appropriate password
4. Update the settings.py PASSWORD field if you set a password

### Option 3: Use Docker MySQL
1. Install Docker Desktop
2. Run: `docker run --name mysql-upg -e MYSQL_ROOT_PASSWORD=yourpassword -p 3306:3306 -d mysql:8.0`
3. Update the settings.py PASSWORD field

## Activation Steps (When Compatible Version Available)

1. **Update settings.py**:
   - Comment out the SQLite configuration
   - Uncomment the MySQL configuration

2. **Create the database**:
   ```bash
   mysql -u root -p
   CREATE DATABASE upg_management_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   EXIT;
   ```

3. **Install MySQL client** (if not already installed):
   ```bash
   pip install mysqlclient
   ```

4. **Run migrations**:
   ```bash
   python manage.py migrate
   ```

5. **Create superuser**:
   ```bash
   python manage.py createsuperuser
   ```

## Backup Files
- `upg_system/settings_mysql_backup.py` - Contains the attempted MySQL configuration
- Current SQLite database: `db.sqlite3` - Contains all existing data

## Benefits of MySQL Migration
- Better performance for larger datasets
- Support for concurrent users
- Advanced query optimization
- Better suited for production deployment
- Supports larger file uploads and data operations

## Testing After Migration
Once MySQL is configured, test these key functionalities:
- Grants dashboard and report generation
- Training attendance tracking
- User authentication and roles
- Data export/import operations

## Rollback Plan
If issues occur after MySQL migration:
1. Comment out MySQL configuration in settings.py
2. Uncomment SQLite configuration
3. Run `python manage.py migrate` to ensure SQLite compatibility
4. System will revert to SQLite with all existing data intact