# MCP Server Implementation Options

## Current State
The server is currently a standard HTTP REST API with a `/api/authorize-decision` endpoint. Agents need to be explicitly told about this endpoint and how to construct requests.

## Option 1: Full MCP Protocol Implementation

Implement the Model Context Protocol to make tools automatically discoverable:

### Requirements:
- Use `mcp` Python SDK or implement JSON-RPC protocol
- Expose tools via `tools/list` method
- Handle `tools/call` requests
- Use stdio or HTTP transport

### Example structure:
```python
# Tools registered with MCP
{
  "name": "evaluate_authorization_decision",
  "description": "Evaluate an authorization decision using PingOne Authorize",
  "inputSchema": {
    "type": "object",
    "properties": {
      "user_id": {"type": "string"},
      "policy_request": {"type": "string"},
      "parameters": {"type": "object"}
    }
  }
}
```

### Libraries needed:
- `mcp` Python SDK (if available)
- Or implement JSON-RPC manually

## Option 2: OpenAPI/Swagger Schema

Expose OpenAPI schema so agents can auto-discover:

- Add FastAPI automatic OpenAPI docs at `/docs`
- Provides interactive schema
- Agents can parse OpenAPI spec

## Option 3: Agent Configuration File

Provide a config file that agents load:

- `agent_config.json` with endpoint, examples, schema
- Agent reads this file to understand capabilities
- Simple but requires manual agent setup

## Recommendation

For true MCP integration, **Option 1** is needed. For simpler HTTP API usage, **Option 2** (OpenAPI) provides good discoverability.

