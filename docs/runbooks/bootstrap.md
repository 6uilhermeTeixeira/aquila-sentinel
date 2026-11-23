# Bootstrap local

1. Execute `python3 scripts/bootstrap.py` uma vez. Guarde `.local/admin_password` fora do repositório e restrinja o acesso ao usuário operador.
2. Execute `docker compose -f compose/compose.yaml up -d`.
3. Confirme o discovery OIDC em `http://127.0.0.1:8080/realms/master/.well-known/openid-configuration`.
4. Inicialize o OpenBao em ambiente controlado com `docker compose -f compose/compose.yaml exec openbao bao operator init`. Distribua as chaves de unseal e o token inicial a custodiantes distintos. Nunca os coloque no Git ou nos logs.
5. Execute `bao operator unseal` com o quórum necessário, via console controlado. Revogue o token inicial após configurar políticas, autenticação e administradores. Configure auditoria antes de permitir acesso de clientes.

Este runbook valida apenas a inicialização local. A produção exige procedimento de recuperação, backup criptografado e teste de restauração.
