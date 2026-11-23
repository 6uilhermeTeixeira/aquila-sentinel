# PRD: `aquila-sentinel`

**Zero-Trust & Identity** · Setor Aquila (Visão, Alerta & Inovação) · Matriz dos 24 Anciãos
**Versão:** 0.1 (rascunho) · **Status:** Em construção · **Responsável:** _(preencher)_

---

## 1. Resumo

O `aquila-sentinel` é a VM de **prevenção** da plataforma. Ela centraliza **identidade, autenticação, segredos, acesso privilegiado, hardening e gestão de postura de segurança** dos servidores. Todas as demais VMs (24 no total) autenticam-se e obtêm segredos por meio dela.

Ela também deve funcionar de forma **standalone**, como produto vendável para PMEs ("Zero-Trust & Identity"), sem depender das outras VMs.

**Nome comercial sugerido:** Identity & Access Shield (nome interno "Sentinel" mantido como marca).

## 2. Objetivos

| # | Objetivo | Métrica de sucesso |
|---|---|---|
| O1 | Ser o provedor único de identidade (SSO/MFA) da plataforma | 100% dos serviços autenticando via OIDC/SAML |
| O2 | Eliminar segredos estáticos em código, arquivos e variáveis | 0 segredos em repositórios; rotação automática ativa |
| O3 | Controlar e gravar todo acesso privilegiado a servidores | 100% dos acessos SSH/admin via broker, com sessão auditada |
| O4 | Manter os servidores em conformidade com um baseline de hardening | ≥ 90% de aderência ao CIS Level 1 (Ubuntu 24.04) |
| O5 | Aplicar o modelo zero-trust entre camadas | Nenhum serviço aceita tráfego sem identidade verificada |
| O6 | Operar como produto independente | Instalável sozinha em ambiente cliente, em até 1 dia |

## 3. Escopo

### Dentro do escopo (v1)
- Identity Provider (SSO, MFA, federação, gestão de usuários e grupos)
- Gestão de segredos e PKI interna (certificados curtos, rotação)
- Acesso privilegiado (PAM) a servidores e bancos, com gravação de sessão
- Hardening e verificação de conformidade (baseline CIS, relatório de desvios)
- Registro de postura de dispositivos/servidores (inventário de agentes)
- Políticas de acesso (quem acessa o quê, quando, de onde)
- Envio de logs de auditoria ao `aquila-oculus`

### Fora do escopo (v1)
- SIEM, detecção e EDR → `aquila-oculus`
- Varredura de vulnerabilidades e threat intelligence → `aquila-recon` (ver questão aberta Q2)
- Firewall perimetral, WAF e DNS → `taurus-mesh`
- Backup → `taurus-storage`
- Anti-phishing e DLP → fase futura (sugerido para `aquila-oculus`, para não sobrecarregar o Sentinel)
- Resposta automatizada a incidentes → `leo-devops` com aprovação humana

> **Motivo:** o Sentinel concentra risco. Cada função adicionada aumenta a superfície de ataque do host mais crítico da plataforma.

## 4. Usuários e personas

| Persona | Necessidade |
|---|---|
| **Administrador de plataforma** | Provisionar usuários, políticas e segredos; acessar servidores com segurança |
| **Engenheiro DevOps / pipeline (`leo-devops`)** | Obter credenciais temporárias de forma programática, sem segredos fixos |
| **Auditor / compliance (`homo-ethic`)** | Consultar trilhas de auditoria e relatórios de conformidade |
| **Cliente final (produto standalone)** | Instalar, configurar SSO/MFA e acesso privilegiado com pouco esforço |
| **Agente de IA (LLM/Agent)** | Receber permissões mínimas, temporárias e auditáveis; nunca credenciais permanentes |

## 5. Arquitetura

### 5.1 Base técnica
- **SO:** Ubuntu Server 24.04 LTS, instalação mínima, sem interface gráfica (derivada do `taurus-seed`).
- **Execução:** serviços em containers (Podman rootless ou Docker) orquestrados por Compose/systemd; um serviço por container, redes internas segregadas.
- **Configuração como código:** Ansible para o host, arquivos Compose versionados neste repositório.
- **Persistência:** PostgreSQL próprio do Sentinel (não compartilhar com `taurus-db`), disco criptografado (LUKS).

### 5.2 Componentes

| Função | Componente recomendado | Alternativa |
|---|---|---|
| Identity Provider (SSO/MFA) | **Keycloak** | authentik, Authelia (mais leve) |
| Segredos e PKI | **HashiCorp Vault** | **OpenBao** (fork de licença aberta) |
| CA interna / certificados curtos | **step-ca** (Smallstep) ou PKI do Vault | — |
| Acesso privilegiado (SSH, DB, K8s) | **Teleport** | Boundary, Pomerium (acesso a apps) |
| Hardening e conformidade | **OpenSCAP** + **Ansible Lockdown (CIS)** + **Lynis** | dev-sec hardening |
| Proteção de força bruta | **CrowdSec** / Fail2ban | — |
| Firewall do host | **nftables** (default deny) | UFW como camada simples |
| Auditoria do host | **auditd** + envio ao Oculus | — |
| Overlay zero-trust (opcional) | **NetBird** / Headscale / OpenZiti | WireGuard puro |
| Policy engine (decisões de acesso) | **OPA** (compartilhado com `homo-ethic`) | Keto (Ory) |

### 5.3 Diagrama lógico

```
                 ┌────────────────────────── aquila-sentinel ─────────────────────────┐
 Usuários /      │  Reverse proxy (TLS, mTLS)                                           │
 Serviços  ────► │    ├─ Keycloak (SSO/MFA) ──► PostgreSQL (próprio)                    │
                 │    ├─ Vault/OpenBao (segredos, PKI) ──► storage Raft                 │
                 │    ├─ Teleport (broker SSH/DB, gravação de sessões)                  │
                 │    └─ OPA (políticas)                                                │
                 │  Agente de conformidade (OpenSCAP/Lynis) ──► relatórios              │
                 │  auditd / logs ──► aquila-oculus (somente envio)                     │
                 └──────────────────────────────────────────────────────────────────────┘
        Snapshots do Vault/DB (criptografados) ──► taurus-storage (outro domínio de falha)
```

## 6. Requisitos funcionais

### 6.1 Identidade (ID)
- **ID-01** SSO via OIDC e SAML para todas as VMs e para o `taurus-portal`.
- **ID-02** MFA obrigatório para administradores (TOTP e WebAuthn/passkey).
- **ID-03** Realms/tenants separados por cliente (multi-tenant) no `taurus-portal`.
- **ID-04** Federação opcional com Google Workspace, Microsoft Entra ID e LDAP/AD do cliente.
- **ID-05** Ciclo de vida: criação, desativação e revisão periódica de acessos (access review).
- **ID-06** Contas de serviço e de agentes de IA tratadas como identidades de primeira classe, com escopo mínimo e expiração.

### 6.2 Segredos e PKI (SEC)
- **SEC-01** Todos os segredos armazenados no cofre; nenhum em Git, imagens ou variáveis estáticas.
- **SEC-02** Credenciais dinâmicas e de curta duração para bancos e serviços (leases com TTL).
- **SEC-03** Autenticação de máquinas no cofre via AppRole/OIDC/identidade do workload (usada pelo `leo-devops`).
- **SEC-04** CA interna emitindo certificados curtos para mTLS entre VMs, com renovação automática.
- **SEC-05** Unseal seguro (Shamir com custódia dividida ou auto-unseal), com procedimento documentado.
- **SEC-06** Rotação programada e sob demanda, com trilha de auditoria.

### 6.3 Acesso privilegiado (PAM)
- **PAM-01** Todo acesso SSH/DB/admin passa pelo broker; SSH direto bloqueado nos demais servidores.
- **PAM-02** Certificados de acesso efêmeros (minutos/horas), emitidos após SSO + MFA.
- **PAM-03** Gravação e reprodução de sessões; trilha enviada ao Oculus.
- **PAM-04** Acesso just-in-time com aprovação para ações sensíveis.
- **PAM-05** Ações do Agent de IA com impacto destrutivo exigem **aprovação humana** (human-in-the-loop).

### 6.4 Hardening e conformidade (HRD)
- **HRD-01** Baseline CIS aplicado por Ansible à golden image (`taurus-seed`) e a toda VM nova.
- **HRD-02** Varredura periódica com OpenSCAP/Lynis; relatório de desvios por servidor.
- **HRD-03** Detecção de _drift_ de configuração, com alerta ao Oculus.
- **HRD-04** Painel de score de conformidade por VM e por cliente.
- **HRD-05** SSH somente por chave/certificado, sem root, sem senha.

### 6.5 Zero-trust (ZT)
- **ZT-01** Princípio "nunca confiar, sempre verificar": toda chamada entre serviços exige identidade (mTLS ou token).
- **ZT-02** Microsegmentação por camada (Taurus, Leo, Homo, Aquila) com regra padrão de negação.
- **ZT-03** Decisões de acesso baseadas em identidade, estado do dispositivo e contexto (horário, origem).
- **ZT-04** Políticas versionadas como código (OPA/Rego) e revisadas por pull request.

### 6.6 Auditoria (AUD)
- **AUD-01** Todo evento de autenticação, acesso a segredo, sessão privilegiada e mudança de política gera log estruturado (JSON).
- **AUD-02** Logs enviados ao `aquila-oculus` e a uma cópia **imutável** fora do domínio de falha.
- **AUD-03** O Oculus tem acesso somente leitura; o Sentinel nunca aceita comandos vindos dele.

## 7. Requisitos não funcionais

| Área | Requisito |
|---|---|
| **Disponibilidade** | Meta de 99,9%; falha do Sentinel não pode derrubar serviços já autenticados (tokens/certificados com tolerância e cache controlado) |
| **Recuperação** | RPO ≤ 1 h, RTO ≤ 4 h; restauração testada trimestralmente a partir de snapshots em `taurus-storage` |
| **Desempenho** | Login SSO < 2 s (p95); emissão de segredo < 200 ms (p95) |
| **Escalabilidade** | v1 em nó único com plano de evolução para 3 nós (Raft do Vault, Keycloak em cluster) |
| **Segurança do host** | Mínimo de pacotes, sem compiladores nem ferramentas ofensivas, atualizações automáticas de segurança, Livepatch se disponível |
| **Rede** | Segmento próprio, acesso administrativo somente via rede de gestão, sem exposição direta à internet exceto o endpoint de SSO |
| **Observabilidade** | Métricas Prometheus exportadas; health checks por serviço |
| **Portabilidade** | Entrega reprodutível (OVA/imagem + repositório); instalação standalone documentada |
| **Licenciamento** | Registrar licença de cada componente (ver seção 11) antes de comercializar |

## 8. Integrações com outras VMs

| VM | Direção | Integração |
|---|---|---|
| `aquila-oculus` | Sentinel → Oculus | Envio de logs de auditoria e eventos (syslog/JSON). Oculus só lê |
| `taurus-seed` | Seed → Sentinel | Golden image já endurecida; o Sentinel verifica a conformidade |
| `taurus-mesh` | Mesh ↔ Sentinel | Reverse proxy/WAF na frente do SSO; DNS interno; mTLS |
| `taurus-storage` | Sentinel → Storage | Snapshots criptografados do Vault e do banco |
| `taurus-portal` | Portal → Sentinel | SSO do cliente; criação de realm/tenant a cada contratação |
| `leo-devops` | DevOps → Sentinel | Credenciais dinâmicas para pipelines; sem segredos fixos |
| `homo-ethic` | Ethic ↔ Sentinel | Políticas OPA compartilhadas; auditoria de acessos |
| `homo-rag` / demais | Serviço → Sentinel | Autenticação OIDC e segredos sob demanda |

## 9. Modo standalone (produto)
- Instalação independente, sem dependência das demais VMs.
- Destinos de log e backup configuráveis (syslog genérico, S3 compatível).
- Assistente de configuração inicial: domínio, certificado, primeiro administrador com MFA.
- Documentação de integração com apps do cliente via OIDC/SAML.

## 10. Segurança desta VM (modelo de ameaças resumido)

| Ameaça | Mitigação |
|---|---|
| Comprometimento do Sentinel (acesso a tudo) | Segmento isolado, mínimo de serviços, acesso admin via PAM com MFA, atualização contínua, monitoramento reforçado |
| Vazamento de chave de unseal/root token | Custódia dividida, root token revogado após bootstrap, uso de tokens com escopo |
| Phishing de administrador | WebAuthn/passkeys obrigatórios para papéis privilegiados |
| Prompt injection em LLM/Agent com acesso a segredos | Agent sem acesso direto ao cofre; credencial efêmera com escopo mínimo; aprovação humana para ações destrutivas |
| Abuso de credencial de serviço | TTL curto, rotação, mTLS, alertas de uso anômalo |
| Perda do Sentinel | Backup testado, procedimento de restauração, acesso de emergência _break-glass_ guardado offline |
| Cadeia de suprimentos (imagens/containers) | Imagens oficiais com versão fixada e digest, verificação de assinatura, varredura de imagens (Trivy) |

## 11. Repositórios de referência (projetos existentes)

> **Verifique licença, versão e manutenção atuais de cada projeto antes de adotar.** Licenças de alguns (em especial Vault e Teleport) mudaram nos últimos anos e afetam o uso comercial.

### Identidade e SSO
- **Keycloak**: https://github.com/keycloak/keycloak (IdP completo; Apache 2.0)
- **authentik**: https://github.com/goauthentik/authentik (IdP moderno, mais simples de operar)
- **Authelia**: https://github.com/authelia/authelia (SSO/MFA leve para proxy reverso)
- **Ory (Kratos/Hydra/Keto)**: https://github.com/ory (componentes de identidade e autorização, em API)

### Segredos e PKI
- **HashiCorp Vault**: https://github.com/hashicorp/vault (licença BSL, confira os termos para uso comercial)
- **OpenBao**: https://github.com/openbao/openbao (fork aberto do Vault, hospedado na Linux Foundation)
- **Smallstep step-ca**: https://github.com/smallstep/certificates (CA interna, certificados curtos, ACME)
- **SOPS**: https://github.com/getsops/sops e **age**: https://github.com/FiloSottile/age (segredos criptografados no Git)

### Acesso privilegiado e zero-trust
- **Teleport**: https://github.com/gravitational/teleport (SSH, DB, K8s com auditoria; verifique a licença da edição Community)
- **HashiCorp Boundary**: https://github.com/hashicorp/boundary
- **Pomerium**: https://github.com/pomerium/pomerium (proxy com identidade para aplicações)
- **NetBird**: https://github.com/netbirdio/netbird (overlay zero-trust sobre WireGuard)
- **Headscale**: https://github.com/juanfont/headscale (controle self-hosted do Tailscale)
- **OpenZiti**: https://github.com/openziti/ziti (rede zero-trust)

### Hardening e conformidade
- **OpenSCAP**: https://github.com/OpenSCAP/openscap
- **ComplianceAsCode/content** (SCAP Security Guide): https://github.com/ComplianceAsCode/content
- **Ansible Lockdown, CIS Ubuntu 24.04**: https://github.com/ansible-lockdown/UBUNTU24-CIS
- **dev-sec ansible-collection-hardening**: https://github.com/dev-sec/ansible-collection-hardening
- **Lynis**: https://github.com/CISOfy/lynis
- **Wazuh (módulo SCA, agentes)**: https://github.com/wazuh/wazuh e https://github.com/wazuh/wazuh-docker (o manager fica no Oculus)

### Defesa do host e políticas
- **CrowdSec**: https://github.com/crowdsecurity/crowdsec
- **Open Policy Agent**: https://github.com/open-policy-agent/opa
- **Trivy** (varredura de imagens e IaC): https://github.com/aquasecurity/trivy
- **osquery**: https://github.com/osquery/osquery (inventário e postura de endpoints)

## 12. Roadmap de construção

| Fase | Entregas | Critério de aceite |
|---|---|---|
| **0. Base** | Ubuntu 24.04 mínimo, disco criptografado, CIS aplicado, SSH por chave, nftables default deny, auditd, atualizações automáticas | Relatório OpenSCAP ≥ 90%; sem portas abertas além das previstas |
| **1. Identidade** | PostgreSQL próprio, Keycloak atrás de proxy com TLS, MFA para admins, realm de administração | Login SSO com MFA funcionando; backup do banco testado |
| **2. Segredos e PKI** | Vault/OpenBao com Raft, unseal documentado, CA interna, AppRole/OIDC para pipelines | Pipeline de teste obtém credencial dinâmica; certificado interno renovado automaticamente |
| **3. Acesso privilegiado** | Teleport, SSH via broker, gravação de sessões, JIT com aprovação | SSH direto bloqueado nas VMs de teste; sessões gravadas e reproduzíveis |
| **4. Zero-trust e políticas** | mTLS entre serviços, microsegmentação, políticas OPA versionadas | Tráfego sem identidade rejeitado em teste |
| **5. Conformidade contínua** | Varreduras agendadas, detecção de drift, painel de score | Alerta gerado ao introduzir desvio proposital |
| **6. Integração** | Logs ao Oculus, snapshots no Storage, SSO no Portal, multi-tenant | Fluxo ponta a ponta: nova compra cria tenant e acesso |
| **7. Standalone** | Instalador e assistente de configuração, documentação do cliente | Instalação limpa em ambiente novo em até 1 dia |

## 13. Estrutura sugerida do repositório

```
aquila-sentinel/
├── README.md
├── PRD.md                      # este arquivo
├── docs/
│   ├── runbooks/               # unseal, restauração, break-glass, rotação
│   ├── threat-model.md
│   └── adr/                    # decisões de arquitetura
├── ansible/
│   ├── inventories/
│   ├── roles/                  # base, hardening, nftables, auditd, podman
│   └── playbooks/
├── compose/
│   ├── keycloak/
│   ├── vault/
│   ├── teleport/
│   ├── opa/
│   └── proxy/
├── policies/                   # OPA/Rego, políticas do Vault, roles do Teleport
├── tests/                      # testes de conformidade e de integração
└── .gitignore                  # nunca versionar segredos, chaves ou dumps
```

**Regras do repositório:** nenhum segredo em texto puro (usar SOPS/age); commits assinados; revisão obrigatória por pull request para qualquer mudança em `policies/` e `ansible/roles/hardening`; imagens com versão e digest fixos.

## 14. Riscos

| Risco | Impacto | Mitigação |
|---|---|---|
| Sentinel acumula papéis demais | Alto | Manter v1 enxuta; mover vulnerabilidades e DLP para outras VMs |
| Mudança de licença de componentes | Médio | Preferir alternativas abertas (OpenBao) e registrar licenças |
| Complexidade operacional (Vault + Keycloak + Teleport) | Médio | Automação por Ansible, runbooks, fases pequenas |
| Ponto único de falha | Alto | Backups testados, plano de evolução para alta disponibilidade, break-glass offline |
| Escopo comercial maior que a equipe | Médio | Lançar primeiro o pacote IdP + segredos como produto mínimo |

## 15. Questões em aberto

- **Q1.** A VM é um servidor único ou terá réplicas desde a v1?
- **Q2.** A gestão de vulnerabilidades (Greenbone) fica no `aquila-recon` ou em módulo separado no Sentinel?
- **Q3.** Vault (BSL) ou OpenBao (aberto) para a versão comercial?
- **Q4.** Qual a escala-alvo inicial (homelab, PME, multi-tenant)?
- **Q5.** Qual hypervisor e rede de gestão serão usados?
- **Q6.** O Agent de IA acessará segredos? Se sim, em que escopo e com qual aprovação?
- **Q7.** O fornecimento aos clientes será por implantação dedicada ou multi-tenant compartilhada?

## 16. Definição de pronto (v1)

- [ ] Fases 0 a 3 concluídas e testadas
- [ ] Relatório de conformidade ≥ 90% (CIS L1)
- [ ] MFA obrigatório para todos os papéis privilegiados
- [ ] Nenhum segredo estático identificado por varredura
- [ ] Restauração a partir de backup testada com sucesso
- [ ] Logs de auditoria chegando ao Oculus e à cópia imutável
- [ ] Runbooks de unseal, rotação e break-glass escritos e ensaiados
- [ ] Modelo de ameaças revisado

---
_Documento vivo: atualize a versão e registre decisões em `docs/adr/` a cada mudança relevante._
