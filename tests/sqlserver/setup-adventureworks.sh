#!/bin/bash
# Setup script for AdventureWorks database in SQL Server container
# This script downloads and restores the AdventureWorks2022 database

set -e

echo "Waiting for SQL Server to start..."
sleep 30

# Wait for SQL Server to be ready
for i in {1..60}; do
    /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "$SA_PASSWORD" -C -Q "SELECT 1" > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "SQL Server is ready!"
        break
    fi
    echo "Waiting for SQL Server... ($i/60)"
    sleep 2
done

# Check if AdventureWorks already exists
DB_EXISTS=$(/opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "$SA_PASSWORD" -C -Q "SET NOCOUNT ON; SELECT COUNT(*) FROM sys.databases WHERE name = 'AdventureWorks2022'" -h -1 | tr -d ' ')

if [ "$DB_EXISTS" -gt 0 ]; then
    echo "AdventureWorks2022 database already exists. Skipping restore."
    exit 0
fi

echo "Downloading AdventureWorks2022 backup..."
cd /var/opt/mssql/backup

# Download AdventureWorks2022 OLTP backup from Microsoft
curl -L -o AdventureWorks2022.bak \
    "https://github.com/Microsoft/sql-server-samples/releases/download/adventureworks/AdventureWorks2022.bak"

echo "Restoring AdventureWorks2022 database..."

# Get the logical file names from the backup
/opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "$SA_PASSWORD" -C -Q "
RESTORE FILELISTONLY FROM DISK = '/var/opt/mssql/backup/AdventureWorks2022.bak'
"

# Restore the database
/opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "$SA_PASSWORD" -C -Q "
RESTORE DATABASE [AdventureWorks2022] 
FROM DISK = '/var/opt/mssql/backup/AdventureWorks2022.bak'
WITH MOVE 'AdventureWorks2022' TO '/var/opt/mssql/data/AdventureWorks2022.mdf',
     MOVE 'AdventureWorks2022_log' TO '/var/opt/mssql/data/AdventureWorks2022_log.ldf',
     REPLACE
"

echo "AdventureWorks2022 database restored successfully!"

# Verify the schemas exist
echo "Verifying schemas..."
/opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "$SA_PASSWORD" -C -d AdventureWorks2022 -Q "
SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA 
WHERE SCHEMA_NAME IN ('HumanResources', 'Person', 'Production', 'Purchasing', 'Sales')
ORDER BY SCHEMA_NAME
"

echo "Setup complete!"

