# Authorize-MCP: PingOne Authorize Policy Decision Server

A minimal FastAPI server for forwarding agent decision requests to PingOne Authorize Policy Decision endpoints. Ready to deploy on Render.

## Features
- `/api/authorize-decision` - POST endpoint for agents to request an authorization decision
- OAuth2 M2M flow using PingOne client credentials (client_secret_basic)
- All PingOne params via environment variables (secure for deployment)

## Quickstart (Local)

1. **Clone the repo**  
2. **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
3. **Set environment variables:**
    - Export vars or use your platform's env settings
4. **Start the server:**
    ```bash
    uvicorn main:app --host 0.0.0.0 --port 10000
    ```

## Deploy to Render
1. **Push to Github**
2. **On Render:**
    - Create a new Web Service from your repo
    - Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
    - Set environment variables
3. **Deploy!**

## Environment Variables
- `PINGONE_CLIENT_ID` - Worker app Client ID
- `PINGONE_CLIENT_SECRET` - Worker app Client Secret
- `PINGONE_ENV_ID` - PingOne Environment ID (used in both token URL and evaluate path)
- `PINGONE_DECISION_ENDPOINT_ID` - Decision Endpoint ID (preferred)
- `PINGONE_DECISION_ID` - Back-compat alias; used if endpoint ID not set
- `PINGONE_AUTH_BASE` - Auth base domain (default: `https://auth.pingone.com`)
- `PINGONE_TOKEN_URL` - Optional explicit token URL; if omitted, server uses `{PINGONE_AUTH_BASE}/{PINGONE_ENV_ID}/as/token`
- `PINGONE_API_BASE` - API base (default: `https://api.pingone.com/v1`)

## Token and Evaluate URLs
- Token (built if `PINGONE_TOKEN_URL` not set):
```
{PINGONE_AUTH_BASE}/{PINGONE_ENV_ID}/as/token
```
- Evaluate:
```
{PINGONE_API_BASE}/environments/{PINGONE_ENV_ID}/decisionEndpoints/{PINGONE_DECISION_ENDPOINT_ID}/evaluate
```

For details, see PingOne docs: Evaluate a Decision Request
(https://apidocs.pingidentity.com/pingone/authorize/v1/api/#post-evaluate-a-decision-request)

