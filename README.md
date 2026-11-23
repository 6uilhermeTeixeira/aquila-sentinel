# Aquila Sentinel

Implementação inicial do [PRD](PRD-aquila-sentinel.md) para identidade, cofre de segredos e política de acesso.

## Ambiente local

Requer Python 3, Docker com Compose e `curl`.

```bash
python3 scripts/bootstrap.py
docker compose -f compose/compose.yaml up -d
./tests/smoke.sh
```

O Keycloak fica em `http://127.0.0.1:8080`, o OpenBao em `http://127.0.0.1:8200` e o OPA em `http://127.0.0.1:8181`. A senha inicial do administrador está em `.local/admin_password`. Os serviços só publicam portas no loopback. Este ambiente usa HTTP local e `start-dev` no Keycloak. Sua finalidade é validar a integração e as políticas antes da implantação segura em Ubuntu.

O OpenBao inicia selado e exige inicialização e unseal conforme [runbook](docs/runbooks/bootstrap.md). A política OPA começa sem concessões. Uma aplicação deve verificar o token OIDC antes de consultar OPA e preencher `subject.verified` com o resultado da validação. Este repositório ainda não fornece o gateway que faz essa verificação.

## Estado do PRD

A entrega cobre uma base local para ID-01, SEC-01 e ZT-04. Os critérios completos de MFA, credenciais dinâmicas, PAM, hardening CIS, mTLS, auditoria, backup e modo standalone permanecem pendentes de implementação e teste. O [registro de arquitetura](docs/adr/0001-initial-stack.md) documenta os limites e as próximas etapas.
