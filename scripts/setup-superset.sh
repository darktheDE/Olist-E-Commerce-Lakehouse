#!/bin/bash
# scripts/setup-superset.sh
set -e

export PYTHONPATH=/app/.venv/lib/python3.10/site-packages:$PYTHONPATH

echo "[INIT] Initializing Apache Superset..."

SUPERSET_CMD="/app/.venv/bin/superset"
if [ ! -f "$SUPERSET_CMD" ]; then
    SUPERSET_CMD="superset"
fi

# Create admin user if it doesn't exist
$SUPERSET_CMD fab create-admin \
              --username "${SUPERSET_ADMIN:-admin}" \
              --firstname Superset \
              --lastname Admin \
              --email admin@fab.org \
              --password "${SUPERSET_PASSWORD:-admin}" || true

# Update Superset DB schema
echo "[INIT] Upgrading Superset database..."
$SUPERSET_CMD db upgrade

# Initialize Superset
echo "[INIT] Setting up roles and permissions..."
$SUPERSET_CMD init

# Register Spark Database
echo "[INIT] Registering Spark Database..."
$SUPERSET_CMD shell < /app/scripts/register_database.py

echo "[SUCCESS] Superset setup is complete."
