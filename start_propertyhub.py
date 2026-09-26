#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
ROOT_ENV_FILE = REPO_ROOT / ".env"
ROOT_ENV_EXAMPLE = REPO_ROOT / ".env.example"
BACKEND_ENV_FILE = REPO_ROOT / "backend" / ".env"
BACKEND_ENV_EXAMPLE = REPO_ROOT / "backend" / ".env.example"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Startet die lokale PropertyHub-Entwicklungsumgebung via Docker Compose."
    )
    parser.add_argument(
        "-d",
        "--detached",
        action="store_true",
        help="Startet die Container im Hintergrund.",
    )
    parser.add_argument(
        "--no-build",
        action="store_true",
        help="Überspringt den Docker-Build beim Start.",
    )
    return parser.parse_args()


def ensure_env_file(target: Path, example: Path) -> bool:
    if target.exists():
        return False
    shutil.copyfile(example, target)
    return True


def read_env_value(path: Path, key: str, default: str) -> str:
    if not path.exists():
        return default

    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        current_key, value = stripped.split("=", 1)
        if current_key == key:
            return value.strip()
    return default


def find_compose_command() -> list[str]:
    for command in (["docker", "compose"], ["docker-compose"]):
        try:
            result = subprocess.run(
                command + ["version"],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
        except FileNotFoundError:
            continue

        if result.returncode == 0:
            return command

    raise SystemExit(
        "Docker Compose wurde nicht gefunden. Bitte installiere Docker Desktop oder docker compose."
    )


def print_access_summary() -> None:
    backend_port = read_env_value(ROOT_ENV_FILE, "BACKEND_PORT", "8000")
    frontend_port = read_env_value(ROOT_ENV_FILE, "FRONTEND_PORT", "5173")
    postgres_port = read_env_value(ROOT_ENV_FILE, "POSTGRES_PORT", "5432")
    redis_port = read_env_value(ROOT_ENV_FILE, "REDIS_PORT", "6379")
    admin_email = read_env_value(BACKEND_ENV_FILE, "BOOTSTRAP_ADMIN_EMAIL", "admin@example.com")
    admin_password = read_env_value(
        BACKEND_ENV_FILE, "BOOTSTRAP_ADMIN_PASSWORD", "change-this-bootstrap-password"
    )
    secret_key = read_env_value(
        BACKEND_ENV_FILE, "SECRET_KEY", "replace-with-a-strong-32-character-secret"
    )

    print()
    print("PropertyHub startet mit folgenden lokalen Endpunkten:")
    print(f"  Frontend:     http://localhost:{frontend_port}")
    print(f"  Backend API:  http://localhost:{backend_port}")
    print(f"  Swagger UI:   http://localhost:{backend_port}/docs")
    print(f"  PostgreSQL:   localhost:{postgres_port}")
    print(f"  Redis:        localhost:{redis_port}")
    print()
    print("Bootstrap-Login:")
    print(f"  E-Mail:       {admin_email}")
    print(f"  Passwort:     {admin_password}")

    if secret_key == "replace-with-a-strong-32-character-secret":
        print()
        print("Hinweis: Bitte setze in backend/.env noch einen echten SECRET_KEY.")

    if admin_password == "change-this-bootstrap-password":
        print("Hinweis: Bitte setze in backend/.env noch ein sicheres BOOTSTRAP_ADMIN_PASSWORD.")


def main() -> int:
    args = parse_args()

    created_root_env = ensure_env_file(ROOT_ENV_FILE, ROOT_ENV_EXAMPLE)
    created_backend_env = ensure_env_file(BACKEND_ENV_FILE, BACKEND_ENV_EXAMPLE)

    if created_root_env:
        print("`.env` wurde aus `.env.example` erstellt.")
    if created_backend_env:
        print("`backend/.env` wurde aus `backend/.env.example` erstellt.")

    compose_command = find_compose_command()
    command = [*compose_command, "up"]

    if not args.no_build:
        command.append("--build")
    if args.detached:
        command.append("--detach")

    print_access_summary()
    print()
    print("Starte PropertyHub via Docker Compose ...")

    try:
        completed = subprocess.run(command, cwd=REPO_ROOT, check=False)
    except KeyboardInterrupt:
        print("\nStart abgebrochen.")
        return 130

    if completed.returncode != 0:
        print(
            "\nDer Start ist fehlgeschlagen. Prüfe Docker, freie Ports und die Container-Logs.",
            file=sys.stderr,
        )
        return completed.returncode

    if args.detached:
        print()
        print("PropertyHub läuft jetzt im Hintergrund.")
        print("Logs anzeigen: docker compose logs -f")
        print("Stoppen:       docker compose down")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
