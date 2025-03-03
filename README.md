# Relay Post - Temporary Email Server

A lightweight, in-memory SMTP server and REST API for temporary email testing and development.

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

- **In-memory storage** - No persistent storage, emails are kept temporarily
- **Auto-cleanup** - Automatically removes emails older than 10 minutes
- **SMTP Server** - Available on port 25
- **REST API** - Available on port 8000
- **Multi-recipient support** - Handle emails with multiple recipients
- **Email parsing** - Extracts subject, body, and other email components

## How to Use

1. **Send an email** to any address at your domain:
   ```
   user@example.com → temp123@your-domain.com
   ```

2. **Retrieve emails** via the REST API:
   ```
   GET http://your-raspberry-pi:8000/check/temp123
   ```

## API Reference

- `GET /check/{username}` - Retrieve emails for the specified username