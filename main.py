from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Any, Dict, Optional
import time
import httpx
from config import settings

app = FastAPI()

# -------------------------
# Pydantic models
# -------------------------

class DecisionSubject(BaseModel):
    # Flexible shape; you can refine according to your policy design
    id: Optional[str] = None
    attributes: Optional[Dict[str, Any]] = None

class DecisionAction(BaseModel):
    name: Optional[str] = None
    attributes: Optional[Dict[str, Any]] = None

class DecisionResource(BaseModel):
    id: Optional[str] = None
    type: Optional[str] = None
    attributes: Optional[Dict[str, Any]] = None

class DecisionEnvironment(BaseModel):
    attributes: Optional[Dict[str, Any]] = None

class DecisionRequest(BaseModel):
    subject: Optional[DecisionSubject] = None
    action: Optional[DecisionAction] = None
    resource: Optional[DecisionResource] = None
    environment: Optional[DecisionEnvironment] = None
    # If your policy expects additional facts, include them as a catch-all
    context: Optional[Dict[str, Any]] = None

class DecisionResponse(BaseModel):
    # This mirrors common PingOne evaluation fields; unknown fields are allowed
    decision: Optional[str] = None
    obligations: Optional[Any] = None
    advice: Optional[Any] = None
    attributes: Optional[Any] = None
    raw: Dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_pingone(cls, payload: Dict[str, Any]) -> "DecisionResponse":
        return cls(
            decision=payload.get("decision"),
            obligations=payload.get("obligations"),
            advice=payload.get("advice"),
            attributes=payload.get("attributes"),
            raw=payload,
        )

# -------------------------
# Token caching
# -------------------------

_cached_token: Optional[str] = None
_token_expires_at: float = 0.0

async def get_pingone_token() -> str:
    global _cached_token, _token_expires_at

    now = time.time()
    if _cached_token and now < _token_expires_at - 30:  # 30s safety buffer
        return _cached_token

    token_url = settings.PINGONE_TOKEN_URL
    client_id = settings.PINGONE_CLIENT_ID
    client_secret = settings.PINGONE_CLIENT_SECRET
    if not all([token_url, client_id, client_secret]):
        raise RuntimeError("Missing PingOne credentials in config or environment variables")

    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    async with httpx.AsyncClient() as client:
        resp = await client.post(token_url, data=data, headers=headers, timeout=30)
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
# Endpoint
# -------------------------

@app.post("/api/authorize-decision")
async def authorize_decision(body: DecisionRequest):
    decision_endpoint_id = settings.PINGONE_DECISION_ENDPOINT_ID or settings.PINGONE_DECISION_ID
    if not settings.PINGONE_ENV_ID or not decision_endpoint_id:
        return JSONResponse({
            "error": "Missing PingOne ENV_ID or DECISION_ENDPOINT_ID in config",
        }, status_code=500)

    try:
        token = await get_pingone_token()
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

    evaluate_url = f"{settings.PINGONE_API_BASE}/environments/{settings.PINGONE_ENV_ID}/decisionEndpoints/{decision_endpoint_id}/evaluate"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(evaluate_url, json=body.dict(exclude_none=True), headers=headers, timeout=30)
        # If PingOne returned non-JSON on error, guard parsing
        try:
            payload = resp.json()
        except ValueError:
            return JSONResponse({
                "error": "Non-JSON response from PingOne",
                "status_code": resp.status_code,
                "text": resp.text,
            }, status_code=502)

        # Return validated response
        decision = DecisionResponse.from_pingone(payload)
        return JSONResponse(content=decision.dict(), status_code=resp.status_code)

    except httpx.HTTPStatusError as he:
        return JSONResponse({
            "error": "PingOne responded with an error",
            "status_code": getattr(he.response, "status_code", None),
            "detail": getattr(he.response, "text", None),
        }, status_code=502)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=502)
