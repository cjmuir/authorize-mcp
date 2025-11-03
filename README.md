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

## MCP Protocol Integration

This server implements the Model Context Protocol (MCP) for automatic agent tool discovery.

### MCP Endpoint
- **URL**: `https://authorize-mcp.onrender.com/mcp`
- **Protocol**: JSON-RPC 2.0 over HTTP

### Available MCP Methods

1. **`initialize`** - Initialize MCP connection
   ```json
   {
     "jsonrpc": "2.0",
     "id": 1,
     "method": "initialize",
     "params": {}
   }
   ```

2. **`tools/list`** - List available tools
   ```json
   {
     "jsonrpc": "2.0",
     "id": 2,
     "method": "tools/list",
     "params": {}
   }
   ```

3. **`tools/call`** - Execute a tool
   ```json
   {
     "jsonrpc": "2.0",
     "id": 3,
     "method": "tools/call",
     "params": {
       "name": "evaluate_authorization_decision",
       "arguments": {
         "user_id": "189d1ef5-676d-493f-b65a-39586024083e",
         "policy_request": "payment",
         "parameters": {
           "Request - Payment.paymentAmount": "3000",
           "Request - Payment.creditorName": "Customer2987",
           "Request - Payment.consentId": "test-consent"
         }
       }
     }
   }
   ```

### Tool: `evaluate_authorization_decision`

Evaluates authorization decisions using PingOne Authorize Policy Decision service.

**Arguments:**
- `user_id` (required): PingOne user ID
- `policy_request` (optional): Type of request (default: "payment")
- `parameters` (optional): Policy-specific parameters object

**Example Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Authorization Decision: PERMIT\n✓ The request is authorized.\n\nFull response: {...}"
      }
    ],
    "isError": false
  }
}
```

### Agent Integration
For AI agents integrating with this MCP server:
- Connect to `/mcp` endpoint using JSON-RPC 2.0
- Call `initialize` first
- Use `tools/list` to discover the `evaluate_authorization_decision` tool
- Call `tools/call` with appropriate arguments

See `AGENT_PROMPT.md` for detailed instructions on constructing requests from natural language queries.

### Legacy HTTP API
The `/api/authorize-decision` endpoint remains available for backward compatibility.

