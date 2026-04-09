#!/bin/sh
set -eu

echo "[init-minio] Waiting for MinIO endpoint..."
until mc alias set local "${MINIO_ENDPOINT:-http://minio:9000}" "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD" >/dev/null 2>&1; do
  sleep 2
done

echo "[init-minio] Creating buckets..."
mc mb --ignore-existing "local/${MINIO_BUCKET_BRONZE:-bronze}"
mc mb --ignore-existing "local/${MINIO_BUCKET_SILVER:-silver}"
mc mb --ignore-existing "local/${MINIO_BUCKET_GOLD:-gold}"

echo "[init-minio] Bucket list:"
mc ls local

echo "[init-minio] Done."
