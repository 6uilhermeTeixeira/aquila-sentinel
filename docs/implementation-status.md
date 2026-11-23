# Estado de implementação do PRD

| Área | Estado | Evidência necessária para concluir |
|---|---|---|
| Identidade | Keycloak, PostgreSQL, realm Sentinel e TOTP inicial | Integração SSO OIDC/SAML e WebAuthn administrativo testados |
| Segredos | OpenBao em Raft, auditoria local, PKI curta e AppRole de pipeline | Credenciais dinâmicas de banco, rotação e auditoria externa testadas |
| PAM | Pendente | Broker, bloqueio de SSH direto e gravação de sessões |
| Hardening | Automação básica pronta | Aplicação CIS em Ubuntu 24.04 e relatório OpenSCAP ≥ 90% |
| Zero Trust | Gateway OIDC validando tokens e OPA com negação padrão | mTLS e microsegmentação entre VMs |
| Auditoria | Log local do OpenBao ativo | Entrega ao Oculus e cópia imutável comprovadas |
| Recuperação | Backup criptografado e restauração isolada de PostgreSQL e Raft testados | Cópia externa e metas RPO/RTO comprovadas |
| Standalone | Pendente | Instalação limpa com TLS e MFA em ambiente cliente |
