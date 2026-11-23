#!/usr/bin/env python3
"""Verify local OpenBao auditing and short-lived PKI issuance."""
import json
from pathlib import Path
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
print("OpenBao ativo, auditoria habilitada e certificado curto emitido.")
