#!/usr/bin/env python3
"""Provision a Keycloak service client with a generated local secret."""
import argparse
import json
import secrets
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "http://127.0.0.1:8080"
SECRET_PATH = ROOT / ".local" / "gateway-client-secret"


def main(token=None):
    if token is None:
        token = bootstrap_admin_token()
    if SECRET_PATH.exists():
        client_secret = SECRET_PATH.read_text().strip()
    else:
        client_secret = secrets.token_urlsafe(48)
        with SECRET_PATH.open("x") as output:
            output.write(client_secret + "\n")
        SECRET_PATH.chmod(0o600)
    provision_client(token, client_secret)


def bootstrap_admin_token():
    admin_password = (ROOT / ".local" / "admin_password").read_text().strip()
    form = urlencode({
        "grant_type": "password", "client_id": "admin-cli",
        "username": "admin", "password": admin_password,
    }).encode()
    request = Request(BASE_URL + "/realms/master/protocol/openid-connect/token",
                      data=form, headers={"Content-Type": "application/x-www-form-urlencoded"})
    with urlopen(request, timeout=15) as response:
        return json.load(response)["access_token"]


def provision_client(token, client_secret):
    client = {
        "clientId": "sentinel-service",
        "enabled": True,
        "protocol": "openid-connect",
        "publicClient": False,
        "serviceAccountsEnabled": True,
        "standardFlowEnabled": False,
        "directAccessGrantsEnabled": False,
        "secret": client_secret,
        "protocolMappers": [{
            "name": "sentinel-gateway-audience",
            "protocol": "openid-connect",
            "protocolMapper": "oidc-audience-mapper",
            "consentRequired": False,
            "config": {
                "included.client.audience": "sentinel-gateway",
                "access.token.claim": "true",
                "id.token.claim": "false",
            },
        }],
    }
    lookup = Request(BASE_URL + "/admin/realms/sentinel/clients?clientId=sentinel-service",
                     headers={"Authorization": f"Bearer {token}"})
    with urlopen(lookup, timeout=15) as response:
        existing = json.load(response)
    if existing:
        client_id = existing[0]["id"]
        remote_secret = Request(
            BASE_URL + f"/admin/realms/sentinel/clients/{client_id}/client-secret",
            headers={"Authorization": f"Bearer {token}"},
        )
        with urlopen(remote_secret, timeout=15) as response:
            active_secret = json.load(response)["value"]
        if active_secret != client_secret:
            raise RuntimeError("Segredo local não corresponde ao cliente existente")
        print("Cliente sentinel-service já provisionado.")
        return
    request = Request(BASE_URL + "/admin/realms/sentinel/clients",
                      data=json.dumps(client).encode(),
                      headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                      method="POST")
    try:
        with urlopen(request, timeout=15) as response:
            if response.status != 201:
                raise RuntimeError("Falha ao criar cliente")
    except HTTPError as error:
        if error.code == 409:
            raise RuntimeError("Cliente já existe sem segredo local. Faça a recuperação administrativa.") from error
        raise
    print("Cliente sentinel-service criado; segredo armazenado em .local/.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--admin-token-file", type=Path, help="Token administrativo obtido com MFA")
    args = parser.parse_args()
    main(args.admin_token_file.read_text().strip() if args.admin_token_file else None)
