# Aquila Sentinel

Implementação inicial do [PRD](PRD-aquila-sentinel.md) para identidade, cofre de segredos e política de acesso.

## Ambiente local

Requer Python 3, Docker com Compose e `curl`.

```bash
python3 scripts/bootstrap.py
docker compose -f compose/compose.yaml up -d
./tests/smoke.sh
python3 scripts/identity_bootstrap.py
python3 tests/identity_smoke.py
python3 scripts/setup_openbao.py
python3 tests/openbao_smoke.py
bash tests/backup_roundtrip.sh
```

O Keycloak fica em `http://127.0.0.1:8080`, o OpenBao em `http://127.0.0.1:8200` e o OPA em `http://127.0.0.1:8181`. A senha inicial do administrador está em `.local/admin_password`. Os serviços só publicam portas no loopback. Este ambiente usa HTTP local e `start-dev` no Keycloak. Sua finalidade é validar a integração e as políticas antes da implantação segura em Ubuntu.

O OpenBao inicia selado. `setup_openbao.py` inicializa o nó local, guarda as chaves em `.local/openbao-init.json`, abre o cofre e habilita auditoria e PKI. O procedimento e os limites constam no [runbook](docs/runbooks/bootstrap.md). A política OPA começa sem concessões. Uma aplicação deve verificar o token OIDC antes de consultar OPA e preencher `subject.verified` com o resultado da validação. Este repositório ainda não fornece o gateway que faz essa verificação.

## Estado do PRD

A entrega cobre uma base local de SSO OIDC, MFA inicial com TOTP, cofre com PKI e auditoria, política OPA, backup criptografado e automação básica de host. As provas de PAM, CIS ≥ 90%, mTLS entre VMs, auditoria externa, recuperação dentro de RPO/RTO e modo standalone permanecem pendentes. O [registro de arquitetura](docs/adr/0001-initial-stack.md) documenta os limites e as próximas etapas.
