#!/bin/bash
# hn-pipeline/generate-env.sh

# Run this script from the root of the project: ./generate-env.sh
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd "${SCRIPT_DIR}/../infra/terraform"

echo "Generating .env file from Terraform outputs..."

# Extract Terraform outputs and write to .env file
echo "PROJECT_ID=$(terraform output -raw project_id)" > ../../.env
echo "GCP_REGION=$(terraform output -raw region)" >> ../../.env
echo "PIPELINE_WORKER_SA=$(terraform output -raw pipeline_worker_service_account_email)" >> ../../.env
echo "BRONZE_BUCKET=$(terraform output -raw bronze_bucket_name)" >> ../../.env
echo "SILVER_BUCKET=$(terraform output -raw silver_bucket_name)" >> ../../.env
echo "GOLD_BUCKET=$(terraform output -raw gold_bucket_name)" >> ../../.env
echo "BRONZE_DATASET=$(terraform output -raw bronze_dataset_id)" >> ../../.env
echo "SILVER_DATASET=$(terraform output -raw silver_dataset_id)" >> ../../.env
echo "GOLD_DATASET=$(terraform output -raw gold_dataset_id)" >> ../../.env
echo "CODE_BUCKET=$(terraform output -raw code_bucket_name)" >> ../../.env
echo "ARTIFACT_REGISTRY_URL=$(terraform output -raw artifact_registry_repo_url)" >> ../../.env

cd ../..

echo ".env file generated successfully:"
echo "---------------------------------"
cat .env
echo "---------------------------------"
