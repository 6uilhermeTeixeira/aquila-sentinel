#!/usr/bin/env python3
"""Exercise Keycloak, gateway, and OPA together using a generated service secret."""
import json
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
BASE = "http://127.0.0.1"
secret = (ROOT / ".local" / "gateway-client-secret").read_text().strip()
form = urlencode({
    "grant_type": "client_credentials",
    "client_id": "sentinel-service",
    "client_secret": secret,
}).encode()
request = Request(BASE + ":8080/realms/sentinel/protocol/openid-connect/token",
                  data=form, headers={"Content-Type": "application/x-www-form-urlencoded"})
with urlopen(request, timeout=15) as response:
    token = json.load(response)["access_token"]


def authorize(resource, action, bearer=token):
    headers = {"Content-Type": "application/json"}
    if bearer:
        headers["Authorization"] = "Bearer " + bearer
    request = Request(BASE + ":8081/authorize",
                      data=json.dumps({"resource": resource, "action": action}).encode(),
                      headers=headers)
    try:
        with urlopen(request, timeout=15) as response:
            return response.status
    except HTTPError as error:
        return error.code


assert authorize("health", "read") == 200
assert authorize("secrets", "read") == 403
assert authorize("health", "read", None) == 401
print("Gateway: permissão mínima aceita; ação extra e ausência de token rejeitadas.")
