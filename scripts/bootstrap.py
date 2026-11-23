#!/usr/bin/env python3
"""Create development bootstrap credentials without putting them in Git."""
from pathlib import Path
import secrets

root = Path(__file__).resolve().parents[1]
local = root / ".local"
local.mkdir(mode=0o700, exist_ok=True)
local.chmod(0o700)
for name in ("db_password", "admin_password"):
    path = local / name
    if path.exists():
        continue
    with path.open("x") as output:
        output.write(secrets.token_urlsafe(48) + "\n")
    path.chmod(0o644)
print("Credenciais criadas em .local/ com permissões restritas.")
