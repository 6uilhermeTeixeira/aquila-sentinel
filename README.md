# Aquila Sentinel

Implementação inicial do [PRD](PRD-aquila-sentinel.md) para identidade, cofre de segredos e política de acesso.

## Ambiente local

Requer Python 3, Docker com Compose, `curl` e `gpg`. Node.js é necessário para os testes unitários do gateway.

```bash
python3 scripts/bootstrap.py
docker compose -f compose/compose.yaml up -d
./tests/smoke.sh
python3 scripts/identity_bootstrap.py
python3 tests/identity_smoke.py
python3 tests/gateway_smoke.py
node --test tests/gateway.test.js
python3 scripts/setup_openbao.py
python3 tests/openbao_smoke.py
bash tests/backup_roundtrip.sh
```

O Keycloak fica em `http://127.0.0.1:8080`, o OpenBao em `http://127.0.0.1:8200` e o OPA em `http://127.0.0.1:8181`. A senha inicial do administrador está em `.local/admin_password`. Os serviços só publicam portas no loopback. Este ambiente usa HTTP local e `start-dev` no Keycloak. Sua finalidade é validar a integração e as políticas antes da implantação segura em Ubuntu.

O OpenBao inicia selado. `setup_openbao.py` inicializa o nó local, guarda as chaves em `.local/openbao-init.json`, abre o cofre e habilita auditoria e PKI. O procedimento e os limites constam no [runbook](docs/runbooks/bootstrap.md). O gateway valida assinatura, emissor, audiência e validade do token OIDC antes de consultar o OPA. A política concede ao cliente de teste somente `health:read` e nega as demais ações. A publicação direta do OPA é local para diagnóstico. O gateway e o Keycloak usam HTTP apenas neste ambiente de desenvolvimento.

## Estado do PRD

A entrega cobre uma base local de SSO OIDC, MFA inicial com TOTP, cofre com PKI, AppRole e auditoria, política OPA, backup criptografado e automação básica de host. As provas de PAM, CIS ≥ 90%, mTLS entre VMs, auditoria externa, recuperação dentro de RPO/RTO e modo standalone permanecem pendentes. O [registro de arquitetura](docs/adr/0001-initial-stack.md) documenta os limites e as próximas etapas.
