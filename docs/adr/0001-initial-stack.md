# ADR 0001 — Base inicial de identidade e políticas

Status: proposta implementada para desenvolvimento local.

O PRD prevê um nó inicial e evolução posterior. A primeira composição executável usa Keycloak com PostgreSQL exclusivo, OpenBao em Raft e OPA com política versionada. O acesso externo no Compose fica limitado ao loopback. As redes internas separam identidade, segredos e políticas. O OPA nega por padrão e só concede acesso quando identidade, prazo e permissão são válidos.

O OpenBao foi escolhido como alternativa aberta para o cofre. A decisão comercial e sua revisão de licença ainda precisam ser formalizadas. O ambiente local mantém HTTP e Keycloak em modo de desenvolvimento para facilitar testes. Uma implantação real exige proxy TLS, certificado e domínio, MFA administrativo, isolamento do host, persistência protegida e logs de auditoria externos.

A definição de pronto do PRD pede fases 0 a 3, enquanto o objetivo O5 depende da fase 4. O aceite de Zero Trust deve incluir a fase 4 e provas de rejeição de tráfego sem identidade.
