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
CHECKPOINT_FILE="gs://${SILVER_BUCKET}/silver/checkpoints/bronze_file_state.json"
TMP_CHECKPOINT="/tmp/bronze_file_state.json"


# Download the existing checkpoint file if it exists, otherwise create an empty JSON object
if gsutil -q stat "${CHECKPOINT_FILE}"; then
  gsutil cp "${CHECKPOINT_FILE}" "${TMP_CHECKPOINT}"
else
  echo "{}" > "${TMP_CHECKPOINT}"
fi

dates_to_process=""

echo "Checking for new or updated data in Bronze bucket..."

# List all date-partitioned directories in the Bronze bucket
for path in $(gsutil ls -d "gs://${BRONZE_BUCKET}/bronze/*/*/*/" 2>/dev/null); do
  ingest_date=$(echo "$path" | awk -F/ '{print $(NF-3)"-"$(NF-2)"-"$(NF-1)}')

  # Count files and total bytes in the directory
  file_count=$(gsutil ls "${path}*" 2>/dev/null | wc -l | tr -d ' ')
  total_bytes=$(gsutil du -s "${path}" | awk '{print $1}')


  # Compare with the checkpoint
  old_count=$(jq -r --arg d "$ingest_date" '.[$d].file_count // empty' "${TMP_CHECKPOINT}")
  old_bytes=$(jq -r --arg d "$ingest_date" '.[$d].total_bytes // empty' "${TMP_CHECKPOINT}")


  # If counts or bytes differ, mark this date for processing
  if [ -z "$old_count" ] || [ "$old_count" != "$file_count" ] || [ "$old_bytes" != "$total_bytes" ]; then
    dates_to_process="${dates_to_process}${ingest_date}\n"
  fi
done

echo "Dates to process:"
dates_to_process=$(echo -e "$dates_to_process" | sort -u)
echo "$dates_to_process"

# If no dates to process, exit
if [ -z "$dates_to_process" ]; then
  echo "No new or updated data to process. Exiting."
  exit 0
fi


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

  # --- 4. Update the checkpoint file ---
  BRONZE_PATH="gs://${BRONZE_BUCKET}/bronze/${ingest_date_path}/"
  file_count=$(gsutil ls "${BRONZE_PATH}*" 2>/dev/null | wc -l | tr -d ' ')
  total_bytes=$(gsutil du -s "${BRONZE_PATH}" | awk '{print $1}')
  jq --arg d "$ingest_date" --arg fc "$file_count" --arg tb "$total_bytes" \
    '.[$d] = {file_count: ($fc | tonumber), total_bytes: ($tb | tonumber)}' \
    "${TMP_CHECKPOINT}" > "${TMP_CHECKPOINT}.tmp" && mv "${TMP_CHECKPOINT}.tmp" "${TMP_CHECKPOINT}"

done

# Upload the updated checkpoint file back to GCS
gsutil cp "${TMP_CHECKPOINT}" "${CHECKPOINT_FILE}"

echo "All unprocessed dates have been processed."
