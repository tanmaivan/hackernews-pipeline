#!/bin/bash
# hn-pipeline/generate-env.sh

# Script to generate a .env file from terraform outputs
# Run this script from the root of the project: ./generate_env.sh
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd "${SCRIPT_DIR}/../infra/terraform"

echo "Generating .env file from Terraform outputs..."

echo "PROJECT_ID=$(terraform output -raw project_id)" > ../../.env
echo "GCP_REGION=$(terraform output -raw region)" >> ../../.env
echo "PIPELINE_WORKER_SA=$(terraform output -raw pipeline_worker_service_account_email)" >> ../../.env

cd ../..

echo ".env file generated successfully:"
echo "---------------------------------"
cat .env
echo "---------------------------------"
