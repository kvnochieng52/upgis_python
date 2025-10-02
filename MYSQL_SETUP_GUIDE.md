# MySQL Setup Guide for UPG Management System

## Prerequisites

1. **Install MySQL Server** (if not already installed)
   - Download from: https://dev.mysql.com/downloads/mysql/
   - During installation, set root password as: `Yimbo001$`
   - Make sure to start MySQL service after installation

2. **Verify MySQL Installation**
   - Open Command Prompt as Administrator
   - Add MySQL to PATH if not already done:
     ```
     set PATH=%PATH%;C:\Program Files\MySQL\MySQL Server 8.0\bin
     ```

## Step 1: Create Database

Open Command Prompt and run:

```bash
mysql -u root -p
```

Enter password: `Yimbo001$`

Then run these commands in MySQL:

```sql
CREATE DATABASE IF NOT EXISTS upg_management_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
SHOW DATABASES;
EXIT;
```

## Step 2: Update Django Settings

1. Open `upg_system/settings.py`
2. Comment out the SQLite configuration
3. Uncomment the MySQL configuration:

```python
# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'upg_management_system',
        'USER': 'root',
        'PASSWORD': 'Yimbo001$',
        'HOST': 'localhost',
        'PORT': '3306',
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}
```

## Step 3: Install MySQL Client (Already Done)

The `mysqlclient` package is already installed in your system.

## Step 4: Migrate to MySQL

Run these commands in the UPG system directory:

```bash
# Create fresh migrations
python manage.py makemigrations

# Apply migrations to MySQL
python manage.py migrate

# Create superuser for MySQL database
python manage.py createsuperuser

# Start server
python manage.py runserver
```

## Troubleshooting

### Common Issues:

1. **"mysql: command not found"**
   - Add MySQL bin directory to Windows PATH
   - Or use full path: `"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe"`

2. **"Access denied for user 'root'"**
   - Verify password is correct: `Yimbo001$`
   - Check if MySQL service is running

3. **"Can't connect to MySQL server"**
   - Start MySQL service: `net start mysql80`
   - Check if MySQL is listening on port 3306

### Alternative Setup Using MySQL Workbench:

1. Open MySQL Workbench
2. Connect to Local instance MySQL80
3. Run this query:
   ```sql
   CREATE DATABASE IF NOT EXISTS upg_management_system
   CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```

## Data Migration from SQLite (Optional)

If you want to preserve existing data from SQLite:

1. **Export data from SQLite:**
   ```bash
   python manage.py dumpdata --natural-foreign --natural-primary --exclude=auth.permission --exclude=contenttypes --indent=2 > data_backup.json
   ```

2. **Switch to MySQL configuration**

3. **Import data to MySQL:**
   ```bash
   python manage.py migrate
   python manage.py loaddata data_backup.json
   ```

## Verification

After switching to MySQL:

1. Visit: http://127.0.0.1:8000
2. Login with your superuser account
3. Check admin panel: http://127.0.0.1:8000/admin
4. Verify all menu items work properly

## Benefits of MySQL

- **Better Performance**: Handles concurrent users better than SQLite
- **Production Ready**: Suitable for deployment
- **Better Data Types**: More robust data handling
- **Backup & Recovery**: Better tools for database management
- **Scalability**: Can handle larger datasets

## Support

If you encounter issues:
1. Check MySQL service status
2. Verify database credentials
3. Check firewall settings
4. Ensure MySQL is listening on correct port (3306)