import sys
import paramiko

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

SERVER_HOST = "80.90.189.13"
SERVER_USER = "root"
SERVER_PASS = r"xzoEGd9,V8V^f#"
PROJECT_DIR = "/home/SocialCompas"

def run():
    print(f"🚀 Подключение к SSH {SERVER_HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(SERVER_HOST, username=SERVER_USER, password=SERVER_PASS, timeout=20)
    
    commands = [
        ("Git Pull", f"cd {PROJECT_DIR} && git pull origin main"),
        ("Build MiniApp Frontend", f"cd {PROJECT_DIR}/miniapp && npm install && npm run build"),
        ("Copy & Reload Nginx Config", f"cp {PROJECT_DIR}/scripts/nginx_socialcompass.conf /etc/nginx/sites-available/socialcompass && ln -sf /etc/nginx/sites-available/socialcompass /etc/nginx/sites-enabled/socialcompass && nginx -t && systemctl reload nginx"),
        ("Docker compose build & up", f"cd {PROJECT_DIR} && docker compose -f docker-compose.prod.yml up -d --build"),
        ("Alembic Upgrade", f"docker exec socialcompas_app alembic upgrade head"),
        ("Import Excel Data", f"docker exec socialcompas_app python scripts/import_excel.py"),
    ]

    for title, cmd in commands:
        print(f"\n--- {title} ---")
        stdin, stdout, stderr = client.exec_command(cmd)
        out = stdout.read().decode('utf-8', errors='ignore')
        err = stderr.read().decode('utf-8', errors='ignore')
        if out:
            print(out.strip())
        if err:
            print(f"[STDERR] {err.strip()}")

    print("\n--- SSH Key for GitHub Secrets ---")
    stdin, stdout, stderr = client.exec_command("cat /root/.ssh/github_actions")
    key = stdout.read().decode('utf-8', errors='ignore').strip()
    print(key)

    client.close()

if __name__ == "__main__":
    run()
