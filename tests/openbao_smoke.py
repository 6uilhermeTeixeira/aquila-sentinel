#!/usr/bin/env python3
"""Verify local OpenBao auditing and short-lived PKI issuance."""
import json
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

root = Path(__file__).resolve().parents[1]
state = json.loads((root / ".local" / "openbao-init.json").read_text())
token = state["root_token"]
base = "http://127.0.0.1:8200/v1"
headers = {"X-Vault-Token": token}
with urlopen(Request(base + "/sys/health"), timeout=10) as response:
    assert response.status == 200
with urlopen(Request(base + "/sys/audit", headers=headers), timeout=10) as response:
    assert "file/" in json.load(response)
request = Request(
    base + "/pki/issue/services",
    data=json.dumps({"common_name": "test.sentinel.local", "ttl": "30m"}).encode(),
    headers={**headers, "Content-Type": "application/json"},
)
with urlopen(request, timeout=10) as response:
    certificate = json.load(response)["data"]["certificate"]
    assert "BEGIN CERTIFICATE" in certificate
with urlopen(Request(base + "/auth/approle/role/pipeline-read/role-id", headers=headers), timeout=10) as response:
    role_id = json.load(response)["data"]["role_id"]
with urlopen(Request(base + "/auth/approle/role/pipeline-read/secret-id", data=b"{}", headers=headers), timeout=10) as response:
    secret_id = json.load(response)["data"]["secret_id"]
login = Request(base + "/auth/approle/login", data=json.dumps({"role_id": role_id, "secret_id": secret_id}).encode(), headers={"Content-Type": "application/json"})
with urlopen(login, timeout=10) as response:
    auth = json.load(response)["auth"]
assert auth["lease_duration"] <= 900
try:
    with urlopen(Request(base + "/sys/mounts", headers={"X-Vault-Token": auth["client_token"]}), timeout=10):
        raise AssertionError("Token de pipeline recebeu acesso administrativo")
except HTTPError as error:
    assert error.code == 403
print("OpenBao ativo, auditoria, PKI e token AppRole de curta duração validados.")
