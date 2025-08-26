#!/bin/bash

# Script to create .env file with proper configuration

echo "Creating .env file with Azure OpenAI settings..."

cat > .env << EOL
# Azure OpenAI Settings
API_TYPE=azure_ad
API_BASE=http://openai.work.iqvia.com/cse/prod/proxy/azure/az-cs-caet-rds-openai-cbex-p01
API_VERSION=2024-08-01-preview
MODEL_NAME=gpt4o
EMBEDDING_MODEL=iqvia_embeddings

# Azure Authentication
TENANT_ID=5989ece0-f90e-40bf-9c79-1a7beccdb861
ACCOUNT_NAME=az-cs-caet-rds-openai-cbex-p01
SERVICE_PRINCIPAL_ID=235f7027-7cae-4bb3-8e97-fbb74c9878d7
SERVICE_PRINCIPAL_SECRET=DQP8Q~wT_zs~10StfMkWT2uy4hYRmb.JzJy2wa2H
AUTH_SCOPE=api://825a47b7-8e55-49b5-99c5-d7ecf65bd64d/.default

# File Paths
REQUIREMENTS_DIR=./Requirements(Input)
RESPONSES_DIR=./Responses
EOL

echo "Creating .env.example file (template for GitHub)..."

cat > .env.example << EOL
# Azure OpenAI Settings
API_TYPE=azure_ad
API_BASE=your_azure_endpoint
API_VERSION=2024-08-01-preview
MODEL_NAME=your_model_name
EMBEDDING_MODEL=your_embedding_model

# Azure Authentication
TENANT_ID=your_tenant_id
ACCOUNT_NAME=your_account_name
SERVICE_PRINCIPAL_ID=your_service_principal_id
SERVICE_PRINCIPAL_SECRET=your_service_principal_secret
AUTH_SCOPE=your_auth_scope

# File Paths
REQUIREMENTS_DIR=./Requirements(Input)
RESPONSES_DIR=./Responses
EOL

# Make the script executable
chmod +x create_env.sh

echo ".env and .env.example files have been created successfully!" 