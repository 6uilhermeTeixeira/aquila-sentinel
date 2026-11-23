#!/usr/bin/env python3
"""Initialize the local OpenBao node and enable audit and PKI engines."""
import json
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / ".local" / "openbao-init.json"
BASE = "http://127.0.0.1:8200/v1"


def request(path, payload=None, token=None):
    data = None if payload is None else json.dumps(payload).encode()
    headers = {"Content-Type": "application/json"}
    if token:
        headers["X-Vault-Token"] = token
    req = Request(BASE + path, data=data, headers=headers)
    try:
        with urlopen(req, timeout=120) as response:
            body = response.read()
            return json.loads(body) if body else {}
    except HTTPError as error:
        if error.code in (400, 404):
            raise RuntimeError(f"OpenBao recusou {path}: HTTP {error.code}: {error.read().decode()}") from error
        raise


def main():
    STATE.parent.mkdir(mode=0o700, exist_ok=True)
    STATE.parent.chmod(0o700)
    for attempt in range(60):
        try:
            initialized = request("/sys/init")["initialized"]
            break
        except (ConnectionError, TimeoutError):
            time.sleep(1)
    else:
        raise RuntimeError("OpenBao não respondeu após 60 segundos")
    if not initialized:
        if STATE.exists():
            raise RuntimeError("Estado local existe, mas OpenBao não está inicializado. Verifique o volume Raft.")
        state = request("/sys/init", {"secret_shares": 3, "secret_threshold": 2})
        with STATE.open("x") as output:
            json.dump(state, output)
        STATE.chmod(0o600)
    else:
        if not STATE.exists():
            raise RuntimeError("OpenBao já inicializado. Forneça as chaves de custódia por procedimento manual.")
        state = json.loads(STATE.read_text())
    if request("/sys/seal-status")["sealed"]:
        for key in state["keys_base64"][:2]:
            request("/sys/unseal", {"key": key})
    for attempt in range(60):
        try:
            request("/sys/health")
            break
        except HTTPError:
            time.sleep(1)
    else:
        raise RuntimeError("OpenBao não ficou ativo após unseal")
    token = state["root_token"]
    audit = request("/sys/audit", token=token)
    if "file/" not in audit:
        raise RuntimeError("Auditoria declarativa não foi ativada")
    mounts = request("/sys/mounts", token=token)
    if "pki/" not in mounts:
        request("/sys/mounts/pki", {"type": "pki", "config": {"max_lease_ttl": "8760h"}}, token)
    certificate_request = Request(BASE + "/pki/ca/pem", headers={"X-Vault-Token": token})
    with urlopen(certificate_request, timeout=10) as response:
        has_ca = bool(response.read().strip())
    if not has_ca:
        request("/pki/root/generate/internal", {"common_name": "sentinel.local", "ttl": "8760h", "key_type": "ec"}, token)
    request("/pki/roles/services", {
        "allowed_domains": "sentinel.local", "allow_subdomains": True,
        "ttl": "1h", "max_ttl": "24h", "key_type": "ec"
    }, token)
    if "kv/" not in mounts:
        request("/sys/mounts/kv", {"type": "kv", "options": {"version": "2"}}, token)
    policy = 'path "kv/data/pipeline/*" { capabilities = ["read"] }'
    request("/sys/policies/acl/pipeline-read", {"policy": policy}, token)
    auth = request("/sys/auth", token=token)
    if "approle/" not in auth:
        request("/sys/auth/approle", {"type": "approle"}, token)
    request("/auth/approle/role/pipeline-read", {
        "token_policies": ["pipeline-read"], "token_ttl": "15m", "token_max_ttl": "1h",
        "secret_id_ttl": "1h", "secret_id_num_uses": 1
    }, token)
    print("OpenBao local inicializado, aberto e com auditoria, PKI e AppRole habilitados.")
    print("Proteja .local/openbao-init.json e retire o token root após criar administradores.")


if __name__ == "__main__":
    main()
