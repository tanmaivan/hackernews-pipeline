#!/bin/bash
# This script uses a self-contained BigQuery script to move data from Bronze to Silver.
# It creates a temporary external table for each run to guarantee the schema and URI are correct.

# Exit immediately if a command exits with a non-zero status.
set -e
set -o pipefail

# Navigate to the Terraform configuration directory
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd "${SCRIPT_DIR}/../infra/terraform"

# --- 1. Configure variables ---
echo "Fetching infrastructure details from Terraform..."

GCP_PROJECT_ID=$(terraform output -raw project_id)
REGION=$(terraform output -raw region)
BRONZE_BUCKET=$(terraform output -raw bronze_bucket_name)
SILVER_BUCKET=$(terraform output -raw silver_bucket_name)
BRONZE_DATASET_ID=$(terraform output -raw bronze_dataset_id)

# Check if any of the required variables are empty
if [ -z "${GCP_PROJECT_ID}" ] || [ -z "${BRONZE_BUCKET}" ] || [ -z "${SILVER_BUCKET}" ] || [ -z "${BRONZE_DATASET_ID}" ]; then
  echo "Error: Could not retrieve outputs from Terraform. Please ensure 'terraform apply' was successful."
  exit 1
fi

echo "GCP Project ID: ${GCP_PROJECT_ID}"
echo "Region: ${REGION}"
echo "Bronze Bucket: ${BRONZE_BUCKET}"
echo "Silver Bucket: ${SILVER_BUCKET}"
echo "Bronze Dataset ID: ${BRONZE_DATASET_ID}"
echo "--------------------------"

# --- 2. Find dates to process (delta logic) ---
echo "Finding dates to process..."
source_dates=$(gsutil ls -d "gs://${BRONZE_BUCKET}/bronze/*/*/*/" 2>/dev/null | awk -F/ '{print $(NF-3)"-"$(NF-2)"-"$(NF-1)}' | grep -E '^[0-9]{4}-[0-9]{2}-[0-9]{2}$' | sort)
processed_dates=$(gsutil ls -d "gs://${SILVER_BUCKET}/silver/items/ingest_date=*/" 2>/dev/null | sed 's|.*ingest_date=||' | sed 's|/||' | sort -u || true)
dates_to_process=$(comm -23 <(echo "${source_dates}") <(echo "${processed_dates}"))

if [ -z "$dates_to_process" ]; then
  echo "All dates are already processed. Exiting."
  exit 0
fi

echo "Dates to be processed:"
echo "$dates_to_process"
echo "--------------------------"

# --- 3. Process each date with a BigQuery multi-statement script ---
for ingest_date in ${dates_to_process}; do
  echo "Processing date: ${ingest_date}"
  ingest_date_path=$(echo "${ingest_date}" | sed 's|-|/|g')

  TEMP_TABLE_NAME="temp_hn_raw_$(echo ${ingest_date} | tr -d '-')"
  SILVER_OUTPUT_PATH="gs://${SILVER_BUCKET}/silver/items/ingest_date=${ingest_date}/"

  BQ_SCRIPT="
    -- Step 1: Create a temporary external table for the specific date
    CREATE OR REPLACE EXTERNAL TABLE \`${GCP_PROJECT_ID}.${BRONZE_DATASET_ID}.${TEMP_TABLE_NAME}\`
    (
      raw_line STRING
    )
    OPTIONS (
      format = 'CSV',
      field_delimiter = '§',
      skip_leading_rows = 0,
      uris = ['gs://${BRONZE_BUCKET}/bronze/${ingest_date_path}/*.jsonl.gz']
    );

    -- Step 2: Export data from the temporary table
    EXPORT DATA OPTIONS(
      uri='${SILVER_OUTPUT_PATH}data_*.parquet',
      format='PARQUET',
      overwrite=true,
      compression='SNAPPY'
    ) AS
    WITH parsed_json AS (
      SELECT SAFE.PARSE_JSON(t.raw_line) AS json_obj, _FILE_NAME
      FROM \`${GCP_PROJECT_ID}.${BRONZE_DATASET_ID}.${TEMP_TABLE_NAME}\` AS t
    )
    SELECT
      SAFE_CAST(JSON_EXTRACT_SCALAR(json_obj, '\$.id') AS INT64) AS item_id,
      JSON_EXTRACT_SCALAR(json_obj, '\$.type') AS item_type,
      JSON_EXTRACT_SCALAR(json_obj, '\$.by') AS author,
      TIMESTAMP_SECONDS(SAFE_CAST(JSON_EXTRACT_SCALAR(json_obj, '\$.time') AS INT64)) as created_at,
      JSON_EXTRACT_SCALAR(json_obj, '\$.title') AS title,
      JSON_EXTRACT_SCALAR(json_obj, '\$.text') AS text_content,
      JSON_EXTRACT_SCALAR(json_obj, '\$.url') AS url,
      SAFE_CAST(JSON_EXTRACT_SCALAR(json_obj, '\$.parent') AS INT64) AS parent_id,
      SAFE_CAST(JSON_EXTRACT_SCALAR(json_obj, '\$.score') AS INT64) AS score,
      SAFE_CAST(JSON_EXTRACT_SCALAR(json_obj, '\$.descendants') AS INT64) AS descendants,
      '${ingest_date}' as ingest_date_str,
      _FILE_NAME as source_file
    FROM parsed_json;
  "

  # Run the entire BigQuery script
  bq query --project_id="${GCP_PROJECT_ID}" --use_legacy_sql=false --format=none "${BQ_SCRIPT}"
  echo "Processing for date ${ingest_date} completed."
  echo "--------------------------"
done

echo "All unprocessed dates have been processed."
