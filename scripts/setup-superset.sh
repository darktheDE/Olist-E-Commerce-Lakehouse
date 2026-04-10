#!/bin/bash
# scripts/setup-superset.sh
set -e

echo "[INIT] Initializing Apache Superset..."

# Create admin user if it doesn't exist
superset fab create-admin \
              --username "${SUPERSET_ADMIN:-admin}" \
              --firstname Superset \
              --lastname Admin \
              --email admin@fab.org \
              --password "${SUPERSET_PASSWORD:-admin}" || true

# Update Superset DB schema
echo "[INIT] Upgrading Superset database..."
superset db upgrade

# Initialize Superset
echo "[INIT] Setting up roles and permissions..."
superset init

# Register Spark Database
echo "[INIT] Registering Spark Database..."
superset shell < /app/scripts/register_database.py

echo "[SUCCESS] Superset setup is complete."
