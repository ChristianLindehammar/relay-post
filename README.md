# Relay Post - Temporary Email Server

A lightweight SMTP server and REST API for temporary email testing and development, using Firebase Realtime Database for storage.

## Quick Start

```bash
# Start the server
docker compose up -d

# Stop the server
docker compose down

# View logs
docker compose logs -f
```

## Key Features

- **Firebase Realtime Database** - Stores emails temporarily with automatic cleanup
- **Auto-cleanup** - Automatically removes emails older than 10 minutes
- **SMTP Server** - Available on port 25
- **REST API** - Available on port 8000
- **Multi-recipient support** - Handle emails with multiple recipients
- **Email parsing** - Extracts subject, body, and other email components

## Configuration

### Firebase Configuration (Required)
Set these environment variables to configure Firebase:

```
FIREBASE_CERT_PATH=/path/to/serviceAccountKey.json
FIREBASE_DB_URL=https://your-project-id.firebaseio.com
```

## Storage Configuration

The application supports multiple storage backends in the following priority order:

1. **Firebase Realtime Database** (if configured):
   ```bash
   FIREBASE_CERT_PATH=/path/to/serviceAccountKey.json
   FIREBASE_DB_URL=https://your-project-id.firebaseio.com
```

## How to Use

1. **Send an email** to any address at your domain:
   ```
   user@example.com → temp123@your-domain.com
   ```

2. **Retrieve emails** via the REST API:
   ```
   GET http://your-server-address:8000/check/temp123
   ```

## API Reference

- `GET /check/{username}` - Retrieve emails for the specified username

## Deployment on Google Cloud (Free Tier)

This hybrid approach leverages Google Cloud's free tier offerings for a cost-effective deployment:

### 1. SMTP Server Component (Google Compute Engine f1-micro)

- **Resources**: 1 shared vCPU, 614MB memory
- **Cost**: $0.00/month (within always-free tier)

#### Deployment Steps:

1. **Create a GCE f1-micro instance**:
   ```bash
   gcloud compute instances create relay-smtp \
     --machine-type=f1-micro \
     --zone=us-central1-a \
     --image-family=debian-11 \
     --image-project=debian-cloud
   ```

2. **Install Docker on the VM**:
   ```bash
   sudo apt-get update
   sudo apt-get install -y docker.io docker-compose
   ```

3. **Configure firewall to allow SMTP traffic**:
   ```bash
   gcloud compute firewall-rules create allow-smtp \
     --allow=tcp:25 \
     --target-tags=relay-smtp \
     --description="Allow incoming SMTP connections"
   ```

4. **Deploy SMTP component**:
   - Create a modified docker-compose file that only runs the SMTP service
   - Configure persistent memory sharing with the API service

### 2. API Component (Cloud Run)

- **Features**: Serverless, auto-scaling to zero when inactive
- **Cost**: $0.00/month (within free tier usage limits)

#### Deployment Steps:

1. **Prepare your API service**:
   ```bash
   # Build a container for just the API portion
   gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/relay-api
   ```

2. **Deploy to Cloud Run**:
   ```bash
   gcloud run deploy relay-api \
     --image gcr.io/YOUR_PROJECT_ID/relay-api \
     --platform managed \
     --allow-unauthenticated \
     --memory=256Mi \
     --set-env-vars="SMTP_SERVER_ADDRESS=YOUR_GCE_INSTANCE_IP"
   ```

3. **Configure communication** between the SMTP server and API service:
   
   #### Setting Up Redis on Google Cloud (Option 1)
   
   Google Memorystore for Redis (Recommended for Production):
   
   ```bash
   # Create a Redis instance (2GB minimum size, starts at ~$30/month)
   gcloud redis instances create relay-post-redis \
     --size=2 \
     --region=us-central1 \
     --redis-version=redis_6_x
   
   # Get the Redis IP address
   gcloud redis instances describe relay-post-redis \
     --region=us-central1 \
     --format='get(host)'
   ```
   
   Then configure your services:
   ```bash
   # For SMTP server (GCE)
   export REDIS_HOST=<redis-ip-from-above>
   
   # For Cloud Run
   gcloud run deploy relay-api \
     --image gcr.io/YOUR_PROJECT_ID/relay-api \
     --set-env-vars="REDIS_HOST=<redis-ip-from-above>"
   ```
   
   Note: Our application handles Redis gracefully, falling back to local storage when Redis isn't available.

### 3. Domain Configuration

1. **Set up DNS records**:
   - Create an MX record pointing to your GCE instance for email receiving
   - Create a CNAME record for your API service

2. **Test the deployment**:
   ```bash
   # Send a test email
   echo "Test email" | mail -s "Test Subject" test@your-domain.com
   
   # Check received emails via API
   curl https://your-api-endpoint.run.app/check/test
   ```

This hybrid approach provides the best of both worlds - persistent SMTP service and cost-efficient API hosting that scales down when not in use.