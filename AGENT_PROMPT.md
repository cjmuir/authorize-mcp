# Agent Prompt: PingOne Authorize Decision Request

## Overview
This MCP server provides access to PingOne Authorize Policy Decision evaluation. You can request authorization decisions by sending policy parameters and user context to the `/api/authorize-decision` endpoint.

## Endpoint
- **URL**: `https://authorize-mcp.onrender.com/api/authorize-decision`
- **Method**: `POST`
- **Content-Type**: `application/json`

## Request Structure

The request must contain two main sections:

### 1. `parameters` (object, required)
Policy-specific parameters that match your PingOne policy configuration. The exact keys depend on your policy, but common patterns include:

- **Policy Request**: The type of request (e.g., "payment", "access", "transfer")
- **Request - {Entity}.{Attribute}**: Entity attributes in dot notation format
  - Example: `"Request - Payment.creditorName"` = the creditor name for a payment
  - Example: `"Request - Payment.paymentAmount"` = the payment amount
  - Example: `"Request - Payment.consentId"` = the consent ID for the payment

### 2. `userContext` (object, required)
User context for the authorization decision:

- **user** (object, required)
  - **id** (string, required): The PingOne user ID

## How to Build a Request from Natural Language

When a user asks for an authorization decision, extract:

1. **User ID**: Identify the user making the request
   - Look for phrases like "user 189d1ef5-676d-493f-b65a-39586024083e" or "for user X"
   - Place in `userContext.user.id`

2. **Policy Request Type**: Determine what kind of authorization is being requested
   - "payment", "access", "transfer", etc.
   - Place in `parameters["Policy Request"]`

3. **Entity Attributes**: Extract any attributes mentioned about the request
   - Payment amount → `parameters["Request - Payment.paymentAmount"]`
   - Creditor name → `parameters["Request - Payment.creditorName"]`
   - Consent ID → `parameters["Request - Payment.consentId"]`
   - Resource type → `parameters["Request - Resource.type"]`
   - Action name → `parameters["Request - Action.name"]`
   - etc.

## Example Requests

### Payment Authorization
**User Question**: "Can user 189d1ef5-676d-493f-b65a-39586024083e make a payment of $3000 to Customer2987 with consent test-consent?"

**Request**:
```json
{
  "parameters": {
    "Policy Request": "payment",
    "Request - Payment.creditorName": "Customer2987",
    "Request - Payment.paymentAmount": "3000",
    "Request - Payment.consentId": "test-consent"
  },
  "userContext": {
    "user": {
      "id": "189d1ef5-676d-493f-b65a-39586024083e"
    }
  }
}
```

### Resource Access
**User Question**: "Can user abc123 access the profile resource with ID user-456?"

**Request**:
```json
{
  "parameters": {
    "Policy Request": "access",
    "Request - Resource.type": "profile",
    "Request - Resource.id": "user-456",
    "Request - Action.name": "read"
  },
  "userContext": {
    "user": {
      "id": "abc123"
    }
  }
}
```

## Response Format

The server returns:

```json
{
  "decision": "PERMIT|DENY|NOT_APPLICABLE|INDETERMINATE",
  "obligations": null | [...],
  "advice": null | [...],
  "attributes": null | {...},
  "raw": {
    // Complete response from PingOne
  }
}
```

- **decision**: The authorization decision
  - `PERMIT`: Request is authorized
  - `DENY`: Request is denied
  - `NOT_APPLICABLE`: No policy matched the request
  - `INDETERMINATE`: An error occurred during evaluation
- **obligations**: Additional obligations returned by the policy (if any)
- **advice**: Advice returned by the policy (if any)
- **attributes**: Attributes returned by the policy (if any)
- **raw**: Complete raw response from PingOne for detailed inspection

## Key Points for Agents

1. **Always include both `parameters` and `userContext`** in your request
2. **User ID is required** - extract it from the user's question or context
3. **Parameter names are case-sensitive** - use exact keys like "Policy Request", "Request - Payment.creditorName"
4. **Dot notation in parameter keys** - Use `"Request - Entity.attribute"` format
5. **Values are typically strings** - Even numeric values may need to be strings depending on policy
6. **Check the `/help` endpoint** - GET `https://authorize-mcp.onrender.com/help` for the latest schema

## Error Handling

If you receive an error response:
- **400**: Invalid JSON body - check your request format
- **500**: Server configuration issue - missing environment variables
- **502**: PingOne API error - check the `detail` field for more information

## Workflow Example

1. User asks: "Can user X make a payment of $Y to Z?"
2. Extract:
   - User ID: X
   - Policy Request: "payment"
   - Payment amount: Y
   - Creditor: Z
3. Build request JSON with these values
4. POST to `/api/authorize-decision`
5. Parse response and communicate the `decision` to the user
6. If `NOT_APPLICABLE`, you may need to adjust parameters based on policy requirements



