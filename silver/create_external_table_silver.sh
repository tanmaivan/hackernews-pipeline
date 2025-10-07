#!/bin/bash
#
# This script automatically creates or replaces a BigQuery External Table
# pointing to partitioned Parquet data in the Silver bucket.
#
# Must be run from the root of the project (hn-pipeline/).
#

set -e
set -o pipefail

echo "Starting Silver Layer External Table creation..."

# Navigate to the Terraform configuration directory
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd "${SCRIPT_DIR}/../infra/terraform"

# --- 1. Configure variables ---
echo "Fetching Terraform outputs..."

GCP_PROJECT_ID=$(terraform output -raw project_id)
SILVER_DATASET_ID=$(terraform output -raw silver_dataset_id)
SILVER_BUCKET=$(terraform output -raw silver_bucket_name)

cd ../..


# --- 2. Check if any of the required variables are empty ---
if [ -z "${GCP_PROJECT_ID}" ] || [ -z "${SILVER_DATASET_ID}" ] || [ -z "${SILVER_BUCKET}" ]; then
  echo "Error: Could not retrieve outputs from Terraform. Please ensure 'terraform apply' was successful."
  exit 1
fi

echo "GCP Project ID: ${GCP_PROJECT_ID}"
echo "Silver Dataset ID: ${SILVER_DATASET_ID}"
echo "Silver Bucket: ${SILVER_BUCKET}"
echo "--------------------------"

# --- 3. Define table name and SQL statement ---
SILVER_TABLE_NAME="stg_hackernews_items"
TABLE_REF="${GCP_PROJECT_ID}.${SILVER_DATASET_ID}.${SILVER_TABLE_NAME}"

CREATE_TABLE_SQL="
CREATE OR REPLACE EXTERNAL TABLE \`${TABLE_REF}\`
WITH PARTITION COLUMNS (
    ingest_date STRING -- This column must match the partitioning scheme in the Silver bucket
)
OPTIONS (
    format = 'PARQUET',
    uris = ['gs://${SILVER_BUCKET}/silver/items/*'],
    hive_partition_uri_prefix = 'gs://${SILVER_BUCKET}/silver/items/',
    require_hive_partition_filter = false
);
"

# --- 4. Execute the SQL statement ---
echo "Creating or updating the external table: ${TABLE_REF}..."

bq query \
    --project_id="${GCP_PROJECT_ID}" \
    --use_legacy_sql=false \
    --format=none \
    "${CREATE_TABLE_SQL}"

echo "External table ${TABLE_REF} created or updated successfully."
echo "--------------------------"

echo "Silver Layer External Table creation completed."
