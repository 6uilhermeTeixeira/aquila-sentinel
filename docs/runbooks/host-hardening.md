# Hardening do host Ubuntu 24.04

Execute o playbook somente em uma VM Ubuntu Server 24.04 preparada para o Sentinel. Defina um operador não root com chave SSH funcional e os CIDRs IPv4 reais da rede de gestão no inventário. O exemplo usa uma rede de documentação e exige substituição antes da aplicação.

```bash
ansible-playbook -i ansible/inventories/example.yml ansible/playbooks/host-base.yml --check --diff
ansible-playbook -i ansible/inventories/example.yml ansible/playbooks/host-base.yml
```

O playbook instala auditd, OpenSCAP, nftables e atualizações automáticas. Ele configura o SSH para chave pública, bloqueia root e senhas, e prepara as regras do firewall. O firewall é validado sintaticamente e permanece inativo até `sentinel_activate_firewall=true`. Para ativá-lo, confirme acesso SSH por uma segunda sessão a partir da rede de gestão e revise as portas públicas permitidas. Em hosts com Docker, UFW ou outras regras nftables, revise a interação com as regras existentes antes da ativação. O serviço gerencia somente a tabela `inet sentinel_filter`.

O playbook não aplica uma coleção CIS completa. Use o conteúdo OpenSCAP do Ubuntu 24.04 aprovado para o ambiente, passe o datastream ao script e analise o relatório. O critério de aderência ≥ 90% do PRD só estará comprovado após a medição em VM representativa.

```bash
sudo ansible/playbooks/scan-openscap.sh /path/to/ssg-ubuntu2404-ds.xml /var/lib/aquila-sentinel/scans/$(date +%F)
```

O relatório pode conter detalhes sensíveis do host. Guarde-o com acesso restrito. A criptografia de disco LUKS e a imagem base `taurus-seed` precisam ser configuradas durante o provisionamento da VM.

Referências oficiais: [Firewall nftables no Ubuntu](https://documentation.ubuntu.com/security/security-features/network/firewall/nftables/), [OpenSSH no Ubuntu](https://ubuntu.com/server/docs/openssh-server/) e [atualizações automáticas](https://ubuntu.com/server/docs/how-to/software/automatic-updates/).
