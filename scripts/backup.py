#!/usr/bin/env python3
"""Encrypted local snapshots of the Sentinel PostgreSQL and OpenBao stores."""
import argparse
from datetime import datetime, timezone
import os
from pathlib import Path
import secrets
import subprocess
import sys
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
COMPOSE = ROOT / "compose" / "compose.yaml"
LOCAL = ROOT / ".local"
PASSPHRASE = LOCAL / "backup_passphrase"
BAO_TOKEN = LOCAL / "bao_token"


def ensure_passphrase() -> None:
    LOCAL.mkdir(mode=0o700, exist_ok=True)
    LOCAL.chmod(0o700)
    if not PASSPHRASE.exists():
        with PASSPHRASE.open("x") as stream:
            stream.write(secrets.token_urlsafe(64) + "\n")
        PASSPHRASE.chmod(0o600)
        print(f"Chave de backup criada em {PASSPHRASE}. Copie-a para custódia offline.", file=sys.stderr)
    if PASSPHRASE.stat().st_mode & 0o077:
        raise SystemExit("A chave de backup deve ter permissão 0600.")


def encrypt_stream(source, destination: Path) -> None:
    partial = destination.with_suffix(destination.suffix + ".partial")
    try:
        with partial.open("xb") as output:
            encrypted = subprocess.Popen(
                ["gpg", "--batch", "--yes", "--pinentry-mode", "loopback",
                 "--passphrase-file", str(PASSPHRASE), "--symmetric",
                 "--cipher-algo", "AES256"],
                stdin=subprocess.PIPE, stdout=output,
            )
            try:
                while chunk := source.read(1024 * 1024):
                    encrypted.stdin.write(chunk)
            except BaseException:
                encrypted.kill()
                encrypted.wait()
                raise
            finally:
                encrypted.stdin.close()
            if encrypted.wait() != 0:
                raise RuntimeError("Falha ao criptografar o snapshot")
        partial.replace(destination)
    except BaseException:
        partial.unlink(missing_ok=True)
        raise


def backup_postgres(destination: Path) -> None:
    dump = subprocess.Popen(
        ["docker", "compose", "-f", str(COMPOSE), "exec", "-T", "-u", "postgres",
         "postgres", "pg_dump", "-Fc", "-U", "keycloak", "keycloak"],
        stdout=subprocess.PIPE,
    )
    try:
        encrypt_stream(dump.stdout, destination)
        if dump.wait() != 0:
            destination.unlink(missing_ok=True)
            raise RuntimeError("pg_dump falhou")
    finally:
        dump.stdout.close()
        if dump.poll() is None:
            dump.kill()
            dump.wait()


def backup_openbao(destination: Path) -> None:
    if not BAO_TOKEN.is_file():
        raise RuntimeError(f"Token de snapshot ausente em {BAO_TOKEN}")
    if BAO_TOKEN.stat().st_mode & 0o077:
        raise RuntimeError("O token OpenBao deve ter permissão 0600.")
    token = BAO_TOKEN.read_text().strip()
    if not token:
        raise RuntimeError("Token de snapshot vazio")
    request = Request("http://127.0.0.1:8200/v1/sys/storage/raft/snapshot",
                      headers={"X-Vault-Token": token})
    with urlopen(request, timeout=120) as response:
        encrypt_stream(response, destination)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("component", choices=["postgres", "openbao", "all"])
    parser.add_argument("--output-dir", type=Path, default=LOCAL / "backups")
    args = parser.parse_args()
    os.umask(0o077)
    ensure_passphrase()
    args.output_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    for component in (["postgres", "openbao"] if args.component == "all" else [args.component]):
        destination = args.output_dir / f"{component}-{timestamp}.gpg"
        if destination.exists():
            raise SystemExit(f"Snapshot já existe: {destination}")
        if component == "postgres":
            backup_postgres(destination)
        else:
            backup_openbao(destination)
        print(destination)


if __name__ == "__main__":
    main()
