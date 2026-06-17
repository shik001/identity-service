# Deployment Instructions

## Identity Service (FastAPI) — Azure Container Apps

### Prerequisites

- Azure subscription
- ACR: `aivideosearchapi` (Basic SKU, Admin user enabled)
- Resource group: `rg-video-search`
- Container Apps Environment: `aca-video-search-env` (already created)

### Step 1: Zip the project on Mac

```bash
cd ~/Projects/i3\ Digital\ Health/identity-service
zip -r "identity-service.zip" . -x ".env" "__pycache__/*" ".git/*" ".venv/*" "tests/*"
```

### Step 2: Upload to Azure Cloud Shell

1. Go to https://shell.azure.com
2. Click **Upload/Download** → **Upload** → select `identity-service.zip`

### Step 3: Build image in ACR (no Docker needed)

```bash
unzip "identity-service.zip" -d identity-service-app
cd identity-service-app

az acr build --registry aivideosearchapi --image identity-service:latest --file "Dockerfile" "."
```

### Step 4: Create the Container App

```bash
az containerapp create \\
  --name identity-service-app \\
  --resource-group rg-video-search \\
  --environment aca-video-search-env \\
  --image aivideosearchapi.azurecr.io/identity-service:latest \\
  --target-port 8000 \\
  --ingress external \\
  --registry-server aivideosearchapi.azurecr.io \\
  --registry-username aivideosearchapi \\
  --registry-password <ACR_PASSWORD> \\
  --env-vars \\
        CONFIG_DB_URI="mongodb+srv://dev22:ZRLttnSOTajTIhxh@cluster0.dbtuf4t.mongodb.net/?appName=Cluster0" \
\
    CONFIG_DB_NAME="identity_config" \\
    JWT_SECRET="change-me-in-production" \\
    CORS_ORIGINS="*"
```

> `<ACR_PASSWORD>` — get from Azure Portal → Container Registries → `aivideosearchapi` → Access keys → Password

### Identity Service Endpoint

After deployment: `https://identity-service-app.<your-unique-id>.centralindia.azurecontainerapps.io`

Swagger UI: `https://identity-service-app.<your-unique-id>.centralindia.azurecontainerapps.io/docs`

### Re-deploying (after code changes)

```bash
# On Mac: zip again, upload fresh zip to Cloud Shell

# In Cloud Shell:
cd identity-service-app
# OR re-unzip:
# unzip "identity-service.zip" -d identity-service-app && cd identity-service-app

az acr build --registry aivideosearchapi --image identity-service:latest --file "Dockerfile" "."

az containerapp update \\
  --name identity-service-app \\
  --resource-group rg-video-search \\
  --image aivideosearchapi.azurecr.io/identity-service:latest
```
