import sys
import os
import time
import paramiko

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

SERVER_HOST = "80.90.189.13"
SERVER_USER = "root"
SERVER_PASS = r"xzoEGd9,V8V^f#"
PROJECT_DIR = "/home/SocialCompas"
GIT_REPO = "https://github.com/GFPC/SocialCompas.git"


def run_ssh_commands():
    print(f"🚀 Подключение к серверу {SERVER_HOST} ({SERVER_USER})...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        client.connect(SERVER_HOST, username=SERVER_USER, password=SERVER_PASS, timeout=20)
        print("✅ Успешное SSH подключение!")

        commands = [
            # 1. Update system packages
            ("Обновление пакетов apt...", "apt-get update -y"),

            # 2. Install Docker, Nginx, Node.js, Certbot
            ("Установка Docker, Nginx, Node.js, Certbot...",
             "apt-get install -y docker.io docker-compose-v2 nginx certbot python3-certbot-nginx nodejs npm curl ufw git"),

            # 3. Enable services
            ("Включение служб Docker и Nginx...", "systemctl enable --now docker nginx"),

            # 4. Create directory and clone repository
            (f"Подготовка директории {PROJECT_DIR} и клонирование репозитория...",
             f"""
             mkdir -p /home
             if [ -d "{PROJECT_DIR}/.git" ]; then
                 cd {PROJECT_DIR} && git pull origin main
             else
                 rm -rf {PROJECT_DIR}
                 git clone {GIT_REPO} {PROJECT_DIR}
             fi
             """),

            # 5. Build MiniApp frontend
            ("Сборка фронтенда React MiniApp...", f"cd {PROJECT_DIR}/miniapp && npm install && npm run build"),

            # 6. Configure Nginx
            ("Настройка Nginx виртуального хоста...", f"""
            cp {PROJECT_DIR}/scripts/nginx_socialcompass.conf /etc/nginx/sites-available/socialcompass
            ln -sf /etc/nginx/sites-available/socialcompass /etc/nginx/sites-enabled/socialcompass
            rm -f /etc/nginx/sites-enabled/default
            nginx -t && systemctl reload nginx
            """),

            # 7. Start Docker Compose production environment
            ("Запуск Docker Compose на сервере...", f"cd {PROJECT_DIR} && docker compose -f docker-compose.prod.yml up -d --build"),

            # 8. Setup SSH Keypair for GitHub Actions CI/CD
            ("Настройка SSH-ключа для GitHub Actions CI/CD...", """
            mkdir -p /root/.ssh
            chmod 700 /root/.ssh
            if [ ! -f /root/.ssh/github_actions ]; then
                ssh-keygen -t rsa -b 4096 -f /root/.ssh/github_actions -N ""
            fi
            cat /root/.ssh/github_actions.pub >> /root/.ssh/authorized_keys
            chmod 600 /root/.ssh/authorized_keys
            """),
        ]

        for desc, cmd in commands:
            print(f"\n▶️ {desc}")
            stdin, stdout, stderr = client.exec_command(cmd)
            out = stdout.read().decode('utf-8', errors='ignore')
            err = stderr.read().decode('utf-8', errors='ignore')
            if out:
                print(out.strip()[:500])
            if err and "warning" not in err.lower() and "notice" not in err.lower():
                print(f"⚠️ {err.strip()[:300]}")

        # Fetch the generated private key for GitHub Secret
        print("\n🔑 Получение приватного SSH-ключа для GitHub Secrets (SERVER_SSH_KEY)...")
        stdin, stdout, stderr = client.exec_command("cat /root/.ssh/github_actions")
        private_key = stdout.read().decode('utf-8', errors='ignore').strip()

        print("\n" + "=" * 60)
        print("🎉 СЕРВЕР 80.90.189.13 УСПЕШНО НАСТРОЕН И ЗАПУЩЕН!")
        print("=" * 60)
        print("\n📋 Скопируйте этот приватный ключ и добавьте его в GitHub Secrets:")
        print("   Имя секретa: SERVER_SSH_KEY")
        print("-" * 60)
        print(private_key)
        print("-" * 60)

    except Exception as e:
        print(f"❌ Ошибка настройки сервера: {e}")
    finally:
        client.close()


if __name__ == "__main__":
    run_ssh_commands()
