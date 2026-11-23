#!/usr/bin/env python3
"""Restore an encrypted snapshot into a new PostgreSQL DB or an isolated OpenBao."""
import argparse
import http.client
import os
from pathlib import Path
from urllib.parse import urlsplit
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
COMPOSE = ROOT / "compose" / "compose.yaml"
PASSPHRASE = ROOT / ".local" / "backup_passphrase"
BAO_TOKEN = ROOT / ".local" / "bao_token"


def decrypt(snapshot: Path) -> subprocess.Popen:
    if not snapshot.is_file() or snapshot.suffix != ".gpg":
        raise SystemExit("Informe um snapshot .gpg existente.")
    if not PASSPHRASE.is_file():
        raise SystemExit(f"Chave de backup ausente: {PASSPHRASE}")
    return subprocess.Popen(
        ["gpg", "--batch", "--yes", "--pinentry-mode", "loopback",
         "--passphrase-file", str(PASSPHRASE), "--decrypt", str(snapshot)],
        stdout=subprocess.PIPE,
    )


def compose_command(*args: str) -> list[str]:
    return ["docker", "compose", "-f", str(COMPOSE), "exec", "-T", "-u", "postgres", "postgres", *args]


def restore_postgres(snapshot: Path, database: str) -> None:
    if not re.fullmatch(r"[a-z][a-z0-9_]{0,62}", database):
        raise SystemExit("Nome do banco inválido. Use letras minúsculas, números e sublinhado.")
    if database == "keycloak":
        raise SystemExit("A restauração exige um banco novo. Não substitua o banco em uso.")
    if not snapshot.is_file() or snapshot.suffix != ".gpg":
        raise SystemExit("Informe um snapshot .gpg existente.")
    if not PASSPHRASE.is_file():
        raise SystemExit(f"Chave de backup ausente: {PASSPHRASE}")
    subprocess.run(compose_command("createdb", "-U", "keycloak", "-O", "keycloak", database), check=True)
    decrypted = decrypt(snapshot)
    try:
        restored = subprocess.run(compose_command("pg_restore", "-U", "keycloak", "-d", database,
                                                  "--no-owner", "--no-acl"), stdin=decrypted.stdout)
        decrypted.stdout.close()
        if decrypted.wait() != 0 or restored.returncode != 0:
            raise RuntimeError("Restauração falhou. O banco novo deve ser inspecionado e removido manualmente.")
    finally:
        decrypted.stdout.close()
        if decrypted.poll() is None:
            decrypted.kill()
            decrypted.wait()
    print(f"Snapshot restaurado em {database}. Valide o conteúdo antes de usá-lo.")


def restore_openbao(snapshot: Path, confirm: str, address: str, token_file: Path) -> None:
    if confirm != "RESTORE_OPENBAO":
        raise SystemExit("Use --confirm RESTORE_OPENBAO apenas em cluster isolado de recuperação.")
    if not token_file.is_file():
        raise SystemExit(f"Token de restauração ausente: {token_file}")
    if token_file.stat().st_mode & 0o077:
        raise SystemExit("O token OpenBao deve ter permissão 0600.")
    token = token_file.read_text().strip()
    if not token:
        raise SystemExit("Token de restauração vazio")
    decrypted = decrypt(snapshot)
    endpoint = urlsplit(address)
    if endpoint.scheme != "http" or endpoint.hostname not in ("127.0.0.1", "localhost"):
        raise SystemExit("A restauração local exige um endereço HTTP de loopback.")
    connection = http.client.HTTPConnection(endpoint.hostname, endpoint.port or 8200, timeout=300)
    try:
        connection.request("POST", "/v1/sys/storage/raft/snapshot-force", body=decrypted.stdout,
                           headers={"X-Vault-Token": token, "Content-Type": "application/octet-stream"},
                           encode_chunked=True)
        response = connection.getresponse()
        response_body = response.read()
        decrypted.stdout.close()
        if decrypted.wait() != 0 or response.status >= 300:
            raise RuntimeError(f"Falha na restauração do OpenBao, HTTP {response.status}: {response_body[:300]!r}")
    finally:
        connection.close()
        decrypted.stdout.close()
        if decrypted.poll() is None:
            decrypted.kill()
            decrypted.wait()
    print("Snapshot OpenBao enviado. Valide a integridade e os serviços no cluster de recuperação.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("component", choices=["postgres", "openbao"])
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("--database", help="Nome de um banco PostgreSQL novo")
    parser.add_argument("--confirm", help="Confirmação explícita para OpenBao")
    parser.add_argument("--address", default="http://127.0.0.1:8200", help="Endpoint OpenBao local")
    parser.add_argument("--token-file", type=Path, default=BAO_TOKEN, help="Arquivo local do token OpenBao")
    args = parser.parse_args()
    os.umask(0o077)
    if args.component == "postgres":
        if not args.database:
            parser.error("--database é obrigatório para PostgreSQL")
        restore_postgres(args.snapshot, args.database)
    else:
        restore_openbao(args.snapshot, args.confirm, args.address, args.token_file)


if __name__ == "__main__":
    main()
