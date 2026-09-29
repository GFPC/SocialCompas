import sys
import os
import paramiko

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

SERVER_HOST = os.getenv("SERVER_HOST", "80.90.189.13")
SERVER_USER = os.getenv("SERVER_USER", "root")
SERVER_PASS = os.getenv("SERVER_PASS", r"***REMOVED***")
PROJECT_DIR = "/home/SocialCompas"


def get_client():
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(SERVER_HOST, username=SERVER_USER, password=SERVER_PASS, timeout=30)
    return c


def exec_cmd(client, title, cmd, ignore_errors=False):
    print(f"\n--- {title} ---")
    try:
        stdin, stdout, stderr = client.exec_command(cmd, timeout=300)
        out = stdout.read().decode('utf-8', errors='ignore').strip()
        err = stderr.read().decode('utf-8', errors='ignore').strip()
        if out:
            print(out)
        if err:
            print(f"[STDERR] {err}")
        exit_code = stdout.channel.recv_exit_status()
        if exit_code != 0 and not ignore_errors:
            print(f"[WARN] Command exited with code {exit_code}")
        return exit_code
    except Exception as exc:
        print(f"[ERR] SSH command failed: {exc}")
        if not ignore_errors:
            raise exc
        return -1


def run():
    print(f"🚀 Подключение к SSH {SERVER_HOST}...")
    client = get_client()

    try:
        # 1. Git pull
        exec_cmd(client, "Git Pull",
                 f"cd {PROJECT_DIR} && git fetch origin && git reset --hard origin/main")

        # 2. Build MiniApp frontend
        exec_cmd(client, "Build MiniApp Frontend",
                 f"cd {PROJECT_DIR}/miniapp && npm install && npm run build")

        # 3. Reload Nginx
        exec_cmd(client, "Copy & Reload Nginx Config",
                 f"cp {PROJECT_DIR}/scripts/nginx_socialcompass.conf /etc/nginx/sites-available/socialcompass"
                 f" && ln -sf /etc/nginx/sites-available/socialcompass /etc/nginx/sites-enabled/socialcompass"
                 f" && nginx -t && systemctl reload nginx")

        # 4. Prune Docker build cache
        exec_cmd(client, "Prune Docker build cache",
                 "docker builder prune -af",
                 ignore_errors=True)

        # 5. Force-remove any zombie container
        exec_cmd(client, "Remove stale socialcompas_app container (if any)",
                 "docker rm -f socialcompas_app 2>/dev/null || true",
                 ignore_errors=True)

        # Re-connect SSH client in case build took long
        client.close()
        client = get_client()

        # 6. Build & start
        exec_cmd(client, "Docker Compose Build & Up",
                 f"cd {PROJECT_DIR} && docker compose -f docker-compose.prod.yml up -d --build")

        # Re-connect SSH client
        client.close()
        client = get_client()

        # 7. Wait for app to be healthy
        exec_cmd(client, "Waiting for app to be healthy",
                 "sleep 8 && docker ps --filter name=socialcompas_app --format '{{.Names}} {{.Status}}'")

        # 8. Alembic migrations
        exec_cmd(client, "Alembic Upgrade",
                 "docker exec socialcompas_app alembic upgrade head")

        # 9. Import Excel data
        exec_cmd(client, "Import Excel Data",
                 "docker exec socialcompas_app python scripts/import_excel.py")

        print("\n✅ Деплой завершён успешно!")
    finally:
        client.close()


if __name__ == "__main__":
    run()
