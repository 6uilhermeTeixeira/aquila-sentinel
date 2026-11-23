# Bootstrap local

1. Execute `python3 scripts/bootstrap.py` uma vez. Guarde `.local/admin_password` fora do repositório e restrinja o acesso ao usuário operador.
2. Execute `docker compose -f compose/compose.yaml up -d`.
3. Confirme o discovery OIDC em `http://127.0.0.1:8080/realms/master/.well-known/openid-configuration`.
4. Execute `python3 scripts/identity_bootstrap.py` para criar o realm Sentinel e exigir TOTP para o administrador inicial.
5. Execute `python3 scripts/setup_openbao.py` para inicializar e abrir o cofre local, ativar auditoria declarativa e configurar a CA local e o papel de certificados curtos. O arquivo `.local/openbao-init.json` contém chaves e token root. Copie-o para custódia separada antes de qualquer limpeza do ambiente.
6. Revogue o token root depois de criar administradores e políticas próprias. Em produção, distribua as chaves de unseal a custodiantes distintos e ensaie o procedimento de emergência.

Este runbook valida apenas a inicialização local. A produção exige procedimento de recuperação, backup criptografado e teste de restauração.
