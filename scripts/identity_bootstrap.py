#!/usr/bin/env python3
"""Create the Sentinel realm and require OTP enrolment for the bootstrap admin."""
import json
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "http://127.0.0.1:8080"
MARKER = ROOT / ".local" / "identity-configured"


def request(method, path, token=None, data=None):
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if data is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(data).encode()
    req = Request(BASE_URL + path, data=data, headers=headers, method=method)
    with urlopen(req, timeout=15) as response:
        body = response.read()
        return json.loads(body) if body else None


def main():
    if MARKER.exists():
        try:
            request("GET", "/realms/sentinel/.well-known/openid-configuration")
        except HTTPError as error:
            if error.code != 404:
                raise
        else:
            if not (ROOT / ".local" / "gateway-client-secret").exists():
                raise RuntimeError("Realm existente sem cliente do gateway; requer recuperação administrativa")
            print("Identidade ja configurada neste ambiente local.")
            return

    password = (ROOT / ".local" / "admin_password").read_text().strip()
    form = urlencode({
        "grant_type": "password",
        "client_id": "admin-cli",
        "username": "admin",
        "password": password,
    }).encode()
    token_request = Request(
        BASE_URL + "/realms/master/protocol/openid-connect/token",
        data=form,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    with urlopen(token_request, timeout=15) as response:
        token = json.load(response)["access_token"]

    realm = json.loads((ROOT / "config/keycloak/sentinel-realm.json").read_text())
    try:
        request("POST", "/admin/realms", token, realm)
    except HTTPError as error:
        if error.code != 409:
            raise

    from gateway_bootstrap import main as configure_gateway_client
    configure_gateway_client(token)

    action = request("GET", "/admin/realms/master/authentication/required-actions/CONFIGURE_TOTP", token)
    action.update(enabled=True, defaultAction=True)
    request("PUT", "/admin/realms/master/authentication/required-actions/CONFIGURE_TOTP", token, action)

    users = request("GET", "/admin/realms/master/users?username=admin&exact=true", token)
    if len(users) != 1:
        raise RuntimeError("Administrador inicial nao encontrado de forma inequivoca")
    admin = users[0]
    admin["requiredActions"] = sorted(set(admin.get("requiredActions", [])) | {"CONFIGURE_TOTP"})
    request("PUT", f"/admin/realms/master/users/{admin['id']}", token, admin)

    MARKER.touch(mode=0o600)
    print("Realm Sentinel criado e TOTP exigido para o administrador inicial.")


if __name__ == "__main__":
    main()
