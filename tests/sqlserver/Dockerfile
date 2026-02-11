# SQL Server with AdventureWorks for Testing
# Uses Microsoft's official SQL Server 2022 image
FROM mcr.microsoft.com/mssql/server:2022-latest

# Switch to root to install packages
USER root

# Install curl for downloading AdventureWorks backup
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Create backup directory
RUN mkdir -p /var/opt/mssql/backup && chown -R mssql:root /var/opt/mssql/backup

# Copy setup script
COPY setup-adventureworks.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/setup-adventureworks.sh

# Switch back to mssql user
USER mssql

# Environment variables
ENV ACCEPT_EULA=Y
ENV MSSQL_SA_PASSWORD=YourPassword123!
ENV SA_PASSWORD=YourPassword123!

# Expose SQL Server port
EXPOSE 1433

# Start SQL Server and run setup script in background
CMD /bin/bash -c '/opt/mssql/bin/sqlservr & /usr/local/bin/setup-adventureworks.sh && wait'

