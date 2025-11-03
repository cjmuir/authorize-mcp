"""
MCP (Model Context Protocol) Server for PingOne Authorize Policy Decisions.

Implements MCP JSON-RPC protocol over HTTP for agent tool discovery and execution.
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Any, Dict, Optional, List
import time
import httpx
import base64
import os
import uuid
from config import settings

app = FastAPI(title="PingOne Authorize MCP Server", version="1.0.0")

DEBUG = os.getenv("DEBUG", "false").lower() in ("1", "true", "yes")

# -------------------------
# MCP Protocol Models
# -------------------------

class JSONRPCRequest(BaseModel):
    """JSON-RPC 2.0 request format."""
    jsonrpc: str = "2.0"
    id: Optional[Any] = None
    method: str
    params: Optional[Dict[str, Any]] = None

class JSONRPCResponse(BaseModel):
    """JSON-RPC 2.0 response format."""
    jsonrpc: str = "2.0"
    id: Optional[Any] = None
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None

class MCPTool(BaseModel):
    """MCP tool definition."""
    name: str
    description: str
    inputSchema: Dict[str, Any]

class MCPToolResult(BaseModel):
    """MCP tool call result."""
    content: List[Dict[str, Any]]
    isError: bool = False

# -------------------------
# Token caching
# -------------------------

_cached_token: Optional[str] = None
_token_expires_at: float = 0.0

async def get_pingone_token() -> str:
    global _cached_token, _token_expires_at

    now = time.time()
    if _cached_token and now < _token_expires_at - 30:
        return _cached_token

    token_url = settings.PINGONE_TOKEN_URL
    if not token_url:
        if not settings.PINGONE_ENV_ID:
            raise RuntimeError("PINGONE_ENV_ID is required to build the token URL")
        token_url = f"{settings.PINGONE_AUTH_BASE.rstrip('/')}/{settings.PINGONE_ENV_ID}/as/token"

    client_id = settings.PINGONE_CLIENT_ID
    client_secret = settings.PINGONE_CLIENT_SECRET
    if not all([token_url, client_id, client_secret]):
        raise RuntimeError("Missing PingOne credentials in config or environment variables")

    basic = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {basic}",
    }
    data = {"grant_type": "client_credentials"}

    if DEBUG:
        print("[DEBUG] Requesting token:", {"token_url": token_url, "auth_method": "client_secret_basic"})

    async with httpx.AsyncClient() as client:
        resp = await client.post(token_url, data=data, headers=headers, timeout=30)
        if DEBUG:
            print("[DEBUG] Token response status:", resp.status_code)
        resp.raise_for_status()
        payload = resp.json()
        token = payload.get("access_token")
        expires_in = payload.get("expires_in", 3600)
        if not token:
            raise RuntimeError("Failed to obtain PingOne access token")

        _cached_token = token
        _token_expires_at = time.time() + int(expires_in)
        return token

# -------------------------
# MCP Protocol Handlers
# -------------------------

async def handle_initialize(params: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Handle MCP initialize request."""
    return {
        "protocolVersion": "2024-11-05",
        "capabilities": {
            "tools": {}
        },
        "serverInfo": {
            "name": "pingone-authorize-mcp",
            "version": "1.0.0"
        }
    }

async def handle_tools_list(params: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Handle MCP tools/list request."""
    return {
        "tools": [
            {
                "name": "evaluate_authorization_decision",
                "description": "Evaluate an authorization decision using PingOne Authorize Policy Decision service. Use this to check if a user is permitted to perform an action (e.g., payment, resource access) based on your PingOne policies.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "PingOne user ID for whom the authorization decision is requested"
                        },
                        "policy_request": {
                            "type": "string",
                            "description": "Type of policy request (e.g., 'payment', 'access', 'transfer')",
                            "default": "payment"
                        },
                        "parameters": {
                            "type": "object",
                            "description": "Policy-specific parameters. Structure depends on your PingOne policy configuration. Common patterns include 'Request - Payment.paymentAmount', 'Request - Payment.creditorName', 'Request - Payment.consentId', etc.",
                            "additionalProperties": True
                        }
                    },
                    "required": ["user_id"]
                }
            }
        ]
    }

async def handle_tools_call(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle MCP tools/call request."""
    tool_name = params.get("name")
    arguments = params.get("arguments", {})

    if tool_name != "evaluate_authorization_decision":
        raise ValueError(f"Unknown tool: {tool_name}")

    user_id = arguments.get("user_id")
    if not user_id:
        raise ValueError("user_id is required")

    policy_request = arguments.get("policy_request", "payment")
    parameters = arguments.get("parameters", {})

    # Ensure Policy Request is in parameters
    if "Policy Request" not in parameters:
        parameters["Policy Request"] = policy_request

    decision_endpoint_id = settings.PINGONE_DECISION_ENDPOINT_ID or settings.PINGONE_DECISION_ID
    if not settings.PINGONE_ENV_ID or not decision_endpoint_id:
        raise RuntimeError("Missing PingOne ENV_ID or DECISION_ENDPOINT_ID in config")

    try:
        token = await get_pingone_token()
    except Exception as e:
        raise RuntimeError(f"Failed to obtain access token: {str(e)}")

    # Build request body for PingOne
    pingone_body = {
        "parameters": parameters,
        "userContext": {
            "user": {
                "id": user_id
            }
        }
    }

    evaluate_url = f"{settings.PINGONE_API_BASE}/environments/{settings.PINGONE_ENV_ID}/decisionEndpoints/{decision_endpoint_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    if DEBUG:
        print("[DEBUG] Calling PingOne evaluate:", {"url": evaluate_url, "has_token": bool(token)})

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(evaluate_url, json=pingone_body, headers=headers, timeout=30)
            payload = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {"text": resp.text}
            
            decision = payload.get("decision", "UNKNOWN")
            result_text = f"Authorization Decision: {decision}\n"
            
            if decision == "PERMIT":
                result_text += "✓ The request is authorized."
            elif decision == "DENY":
                result_text += "✗ The request is denied."
            elif decision == "NOT_APPLICABLE":
                result_text += "⚠ No policy matched this request."
            else:
                result_text += f"⚠ Decision status: {decision}"

            return {
                "content": [
                    {
                        "type": "text",
                        "text": result_text + f"\n\nFull response: {payload}"
                    }
                ],
                "isError": False
            }
    except httpx.HTTPStatusError as he:
        error_text = f"PingOne API error: {he.response.status_code}\n{he.response.text}"
        return {
            "content": [
                {
                    "type": "text",
                    "text": error_text
                }
            ],
            "isError": True
        }
    except Exception as e:
        error_text = f"Error calling PingOne: {str(e)}"
        return {
            "content": [
                {
                    "type": "text",
                    "text": error_text
                }
            ],
            "isError": True
        }

# -------------------------
# MCP JSON-RPC Endpoint
# -------------------------

@app.post("/mcp")
async def mcp_endpoint(request: Request):
    """Main MCP JSON-RPC endpoint."""
    try:
        body = await request.json()
        rpc_request = JSONRPCRequest(**body)
    except Exception as e:
        return JSONResponse(
            content=JSONRPCResponse(
                id=None,
                error={"code": -32700, "message": "Parse error", "data": str(e)}
            ).dict(exclude_none=True),
            status_code=200
        )

    # Handle different MCP methods
    try:
        if rpc_request.method == "initialize":
            result = await handle_initialize(rpc_request.params)
        elif rpc_request.method == "tools/list":
            result = await handle_tools_list(rpc_request.params)
        elif rpc_request.method == "tools/call":
            result = await handle_tools_call(rpc_request.params or {})
        else:
            raise ValueError(f"Unknown method: {rpc_request.method}")

        response = JSONRPCResponse(
            id=rpc_request.id,
            result=result
        )
    except Exception as e:
        response = JSONRPCResponse(
            id=rpc_request.id,
            error={
                "code": -32000,
                "message": "Server error",
                "data": str(e)
            }
        )

    return JSONResponse(content=response.dict(exclude_none=True), status_code=200)

# -------------------------
# Legacy HTTP API (for backward compatibility)
# -------------------------

@app.post("/api/authorize-decision")
async def authorize_decision_legacy(request: Request):
    """Legacy HTTP API endpoint for backward compatibility."""
    try:
        body: Dict[str, Any] = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON body"}, status_code=400)

    decision_endpoint_id = settings.PINGONE_DECISION_ENDPOINT_ID or settings.PINGONE_DECISION_ID
    if not settings.PINGONE_ENV_ID or not decision_endpoint_id:
        return JSONResponse({
            "error": "Missing PingOne ENV_ID or DECISION_ENDPOINT_ID in config",
        }, status_code=500)

    try:
        token = await get_pingone_token()
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

    evaluate_url = f"{settings.PINGONE_API_BASE}/environments/{settings.PINGONE_ENV_ID}/decisionEndpoints/{decision_endpoint_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(evaluate_url, json=body, headers=headers, timeout=30)
        payload = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {"text": resp.text}
        return JSONResponse(content=payload, status_code=resp.status_code)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=502)

# -------------------------
# Help endpoints
# -------------------------

@app.get("/help")
@app.get("/schema")
async def help_schema():
    """Returns API documentation and schema."""
    return JSONResponse({
        "mcp_endpoint": "/mcp",
        "legacy_endpoint": "/api/authorize-decision",
        "description": "PingOne Authorize Policy Decision MCP Server",
        "protocol": "MCP (Model Context Protocol) JSON-RPC over HTTP",
        "tool": {
            "name": "evaluate_authorization_decision",
            "description": "Evaluate authorization decisions using PingOne Authorize"
        }
    })
