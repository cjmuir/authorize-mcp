# Authorize-MCP: PingOne Authorize Policy Decision Server

A minimal FastAPI server for forwarding agent decision requests to PingOne Authorize Policy Decision endpoints. Ready to deploy on Render.

## Features
- `/api/authorize-decision` - POST endpoint for agents to request an authorization decision
- OAuth2 M2M flow using PingOne client credentials
- All PingOne params via environment variables (secure for deployment)

## Quickstart (Local)

1. **Clone the repo**  
2. **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
3. **Set environment variables:**
    - Copy `.env.example` to `.env` and fill your secrets, or export vars directly for dev/testing
4. **Start the server:**
    ```bash
    uvicorn main:app --host 0.0.0.0 --port 10000
    ```

## Deploy to Render
1. **Push to Github**
2. **On Render:**
    - Create a new [Web Service](https://dashboard.render.com/new/web) from your repo
    - Use `uvicorn main:app --host 0.0.0.0 --port 10000` as the Start Command
    - Set environment variables (`PINGONE_CLIENT_ID`, `..._SECRET`, `..._ENV_ID`, `PINGONE_DECISION_ENDPOINT_ID`, `..._TOKEN_URL`, `PINGONE_API_BASE`) in the dashboard
3. **Deploy!**

## Environment Variables
- `PINGONE_CLIENT_ID` - Your PingOne Worker app Client ID
- `PINGONE_CLIENT_SECRET` - Your PingOne Worker app Client Secret
- `PINGONE_ENV_ID` - Your PingOne Environment ID
- `PINGONE_DECISION_ENDPOINT_ID` - Your PingOne Decision Endpoint ID (preferred)
- `PINGONE_DECISION_ID` - Back-compat alias; used if `PINGONE_DECISION_ENDPOINT_ID` not set
- `PINGONE_TOKEN_URL` - PingOne OAuth2 Token URL (default: `https://auth.pingone.com/as/token`)
- `PINGONE_API_BASE` - API base (default: `https://api.pingone.com/v1`)

## Evaluate Endpoint
This server calls:
```
{PINGONE_API_BASE}/environments/{PINGONE_ENV_ID}/decisionEndpoints/{PINGONE_DECISION_ENDPOINT_ID}/evaluate
```
See PingOne docs: Evaluate a Decision Request
(https://apidocs.pingidentity.com/pingone/authorize/v1/api/#post-evaluate-a-decision-request)

