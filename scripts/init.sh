#!/bin/bash
set -e

echo "Initializing AI Influencer Platform..."

# Wait for PostgreSQL
echo "Waiting for PostgreSQL..."
until PGPASSWORD=$POSTGRES_PASSWORD psql -h postgres -U $POSTGRES_USER -d $POSTGRES_DB -c '\q'; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 1
done
echo "PostgreSQL is up!"

# Wait for Redis
echo "Waiting for Redis..."
until redis-cli -h redis -a $REDIS_PASSWORD ping; do
  echo "Redis is unavailable - sleeping"
  sleep 1
done
echo "Redis is up!"

# Wait for MinIO
echo "Waiting for MinIO..."
until curl -f http://minio:9000/minio/health/live; do
  echo "MinIO is unavailable - sleeping"
  sleep 1
done
echo "MinIO is up!"

# Create S3 bucket if it doesn't exist
echo "Creating S3 bucket..."
python3 << EOF
import boto3
from botocore.exceptions import ClientError

s3 = boto3.client(
    's3',
    endpoint_url='$S3_ENDPOINT',
    aws_access_key_id='$S3_ACCESS_KEY',
    aws_secret_access_key='$S3_SECRET_KEY'
)

try:
    s3.create_bucket(Bucket='$S3_BUCKET_NAME')
    print(f"Bucket '$S3_BUCKET_NAME' created")
except ClientError as e:
    if e.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
        print(f"Bucket '$S3_BUCKET_NAME' already exists")
    else:
        raise
EOF

# Wait for Meilisearch
echo "Waiting for Meilisearch..."
until curl -f $MEILISEARCH_URL/health; do
  echo "Meilisearch is unavailable - sleeping"
  sleep 1
done
echo "Meilisearch is up!"

# Create Meilisearch indexes
echo "Creating Meilisearch indexes..."
python3 << EOF
import meilisearch

client = meilisearch.Client('$MEILISEARCH_URL', '$MEILISEARCH_API_KEY')

# Influencers index
try:
    client.create_index('influencers', {'primaryKey': 'id'})
    print("Created influencers index")
except meilisearch.errors.MeiliSearchApiError:
    print("Influencers index already exists")

# Content index
try:
    client.create_index('content', {'primaryKey': 'id'})
    print("Created content index")
except meilisearch.errors.MeiliSearchApiError:
    print("Content index already exists")
EOF

echo "Initialization complete!"
