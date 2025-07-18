#!/bin/bash

# Setup PgAdmin with pre-configured database connection
echo "🔧 Setting up PgAdmin with auto-connect configuration..."

# Create pgadmin config directory if not exists
mkdir -p pgadmin

# Create servers.json for auto server configuration
cat > pgadmin/servers.json << 'EOF'
{
  "Servers": {
    "1": {
      "Name": "TestManager Database",
      "Group": "Servers",
      "Host": "testmanager_postgres",
      "Port": 5432,
      "MaintenanceDB": "testmanager_db",
      "Username": "testmanager_user",
      "PassFile": "/pgpass",
      "SSLMode": "prefer"
    }
  }
}
EOF

# Create pgpass file for automatic authentication  
cat > pgadmin/pgpass << 'EOF'
testmanager_postgres:5432:*:testmanager_user:testmanager_password
EOF

# Set correct permissions for pgpass file
chmod 600 pgadmin/pgpass

echo "✅ PgAdmin configuration files created!"
echo "📋 Files created:"
echo "   - pgadmin/servers.json (server configuration)"
echo "   - pgadmin/pgpass (password file)"
echo ""
echo "🔄 Restart PgAdmin to apply:"
echo "   docker-compose restart pgadmin" 