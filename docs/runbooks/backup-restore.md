# Backup e restauração locais

As rotinas abaixo são para o ambiente Compose. Os arquivos de backup são criptografados com GPG AES-256 durante a captura, sem despejo intermediário em texto puro. A primeira execução cria `.local/backup_passphrase` com permissão 0600. Copie essa chave para custódia offline separada dos backups e verifique a leitura da cópia. Sem ela, os backups não poderão ser restaurados. `.local/` já está fora do Git.

## PostgreSQL

Execute `python3 scripts/backup.py postgres`. O arquivo aparece em `.local/backups/postgres-<data>.gpg`. Para restaurar, escolha um nome de banco novo e execute `python3 scripts/restore.py postgres .local/backups/<arquivo>.gpg --database keycloak_restore_YYYYMMDD`. O script preserva o banco `keycloak` em uso. Compare as tabelas e dados antes de apontar o Keycloak para o banco restaurado. O teste `tests/backup_roundtrip.sh` automatiza essa verificação em um banco temporário.

## OpenBao

Depois de inicializar e abrir o cofre, coloque um token com permissão de snapshot em `.local/bao_token`, com permissão 0600. Execute `python3 scripts/backup.py openbao`. Para restauração, use somente um cluster isolado de recuperação, inicialmente aberto e com token autorizado no arquivo local. Execute `python3 scripts/restore.py openbao .local/backups/<arquivo>.gpg --confirm RESTORE_OPENBAO`. O endpoint de restauração forçada substitui o estado Raft do destino. Depois da importação, use as chaves de unseal do snapshot de origem. O teste local em um contêiner isolado restaurou o snapshot e abriu o cofre com essas chaves. Ainda é necessário ensaiar o procedimento completo em infraestrutura representativa para contabilizar o requisito de recuperação do PRD.

Backups locais não cumprem sozinhos RPO de 1 hora, RTO de 4 horas nem cópia imutável fora do domínio de falha. A automação de envio para armazenamento externo e a prova de recuperação permanecem pendentes.
