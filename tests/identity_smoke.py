#!/usr/bin/env python3
"""Check realm discovery and reject bootstrap-admin password-only login."""
import json
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

root = Path(__file__).resolve().parents[1]
base = "http://127.0.0.1:8080"
with urlopen(base + "/realms/sentinel/.well-known/openid-configuration", timeout=15) as response:
    discovery = json.load(response)
assert discovery["issuer"].endswith("/realms/sentinel"), discovery["issuer"]

password = (root / ".local" / "admin_password").read_text().strip()
form = urlencode({
    "grant_type": "password",
    "client_id": "admin-cli",
    "username": "admin",
    "password": password,
}).encode()
request = Request(
    base + "/realms/master/protocol/openid-connect/token",
    data=form,
    headers={"Content-Type": "application/x-www-form-urlencoded"},
)
try:
    with urlopen(request, timeout=15):
        raise AssertionError("Password-only login was accepted")
except HTTPError as error:
    assert error.code == 400, error.code
print("Discovery OIDC disponivel; login administrativo apenas com senha rejeitado.")
