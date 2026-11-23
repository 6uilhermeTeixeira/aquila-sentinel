# Estado de implementação do PRD

| Área | Estado | Evidência necessária para concluir |
|---|---|---|
| Identidade | Base local de Keycloak e PostgreSQL | Realm, SSO OIDC/SAML e MFA administrativo testados |
| Segredos | OpenBao em Raft, inicialização manual | PKI, credenciais dinâmicas, rotação e auditoria testadas |
| PAM | Pendente | Broker, bloqueio de SSH direto e gravação de sessões |
| Hardening | Pendente | Aplicação CIS em Ubuntu 24.04 e relatório OpenSCAP ≥ 90% |
| Zero Trust | Política OPA padrão de negação | Verificação de token em gateway, mTLS e microsegmentação entre VMs |
| Auditoria | Pendente | Entrega ao Oculus e cópia imutável comprovadas |
| Recuperação | Pendente | Backup e restauração de banco e Raft comprovados |
| Standalone | Pendente | Instalação limpa com TLS e MFA em ambiente cliente |
