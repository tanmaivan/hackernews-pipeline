#!/bin/bash
# hn-pipeline/generate-env.sh

# Script to generate a .env file from terraform outputs
# Run this script from the root of the project: ./generate-env.sh

cd infra/terraform || { echo "Directory infra/terraform not found!"; exit 1; }

echo "Generating .env file from Terraform outputs..."

echo "PROJECT_ID=$(terraform output -raw project_id)" > ../../.env
echo "GCP_REGION=$(terraform output -raw region)" >> ../../.env
echo "PIPELINE_RUNNER_SA=$(terraform output -raw pipeline_runner_service_account_email)" >> ../../.env
echo "EXTRACTOR_IMAGE_PATH=$(terraform output -raw extractor_image_url)" >> ../../.env

cd ../..

echo ".env file generated successfully:"
echo "---------------------------------"
cat .env
echo "---------------------------------"
