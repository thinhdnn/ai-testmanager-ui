# Connect PgAdmin to Database

## Access PgAdmin
1. Open browser: **http://localhost:5050**
2. Login with:
   - **Email**: `admin@testmanager.com`
   - **Password**: `admin123`

## Add Database Server (If Not Auto-Connected)

**Right-click "Servers" → "Register" → "Server"**

### General Tab:
- **Name**: `TestManager Database`

### Connection Tab:
- **Host**: `testmanager_postgres`
- **Port**: `5432`
- **Database**: `testmanager_db`
- **Username**: `testmanager_user`
- **Password**: `testmanager_password`

### Options:
- ✅ **Save Password**: Check this box to remember password

Click **Save** to connect!

## Quick Copy-Paste Values:
```
Host: testmanager_postgres
Port: 5432
Database: testmanager_db
Username: testmanager_user
Password: testmanager_password
```

## View Tables:
After connecting, navigate to:
**TestManager Database → Databases → testmanager_db → Schemas → public → Tables**

You should see all your tables like:
- users
- projects  
- test_cases
- steps
- fixtures
- etc. 