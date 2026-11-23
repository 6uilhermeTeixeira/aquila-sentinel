#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 - <<'PY'
from pathlib import Path
playbook = Path('ansible/playbooks/host-base.yml').read_text()
firewall = Path('ansible/templates/sentinel.nft.j2').read_text()
assert 'sentinel_activate_firewall: false' in playbook
assert 'PasswordAuthentication no' in playbook
assert 'PermitRootLogin no' in playbook
assert 'policy drop' in firewall
assert 'sentinel_management_cidrs' in firewall
PY
bash -n ansible/playbooks/scan-openscap.sh
