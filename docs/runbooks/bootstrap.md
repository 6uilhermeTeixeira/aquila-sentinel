# Bootstrap local

1. Execute `python3 scripts/bootstrap.py` uma vez. Guarde `.local/admin_password` fora do repositório e restrinja o acesso ao usuário operador.
2. Execute `docker compose -f compose/compose.yaml up -d`.
3. Confirme o discovery OIDC em `http://127.0.0.1:8080/realms/master/.well-known/openid-configuration`.
4. Execute `python3 scripts/identity_bootstrap.py` para criar o realm Sentinel e exigir TOTP para o administrador inicial.
5. Execute `python3 scripts/setup_openbao.py` para inicializar e abrir o cofre local, ativar auditoria declarativa, configurar a CA local, certificados curtos e AppRole de pipeline com token de 15 minutos. O arquivo `.local/openbao-init.json` contém chaves e token root. Copie-o para custódia separada antes de qualquer limpeza do ambiente.
6. Revogue o token root depois de criar administradores e políticas próprias. Em produção, distribua as chaves de unseal a custodiantes distintos e ensaie o procedimento de emergência.

Este runbook valida apenas a inicialização local. A produção exige procedimento de recuperação, backup criptografado e teste de restauração.

Em uma instalação local criada antes da inclusão do gateway, o administrador já pode estar sujeito a MFA. Nesse caso, obtenha um token administrativo por um fluxo com MFA, salve-o temporariamente em arquivo 0600 fora do Git e execute `python3 scripts/gateway_bootstrap.py --admin-token-file /caminho/do/token`. Remova o arquivo do token ao terminar. O bootstrap novo cria o cliente antes de exigir MFA e dispensa esse passo.
