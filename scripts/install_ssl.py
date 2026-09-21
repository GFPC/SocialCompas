import sys
import paramiko

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

SERVER_HOST = "80.90.189.13"
SERVER_USER = "root"
SERVER_PASS = r"xzoEGd9,V8V^f#"
DOMAIN = "socialcompass.ru"
EMAIL = "admin@socialcompass.ru"

def run():
    print(f"🚀 Подключение к SSH {SERVER_HOST} для установки SSL-сертификатов...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(SERVER_HOST, username=SERVER_USER, password=SERVER_PASS, timeout=20)

    commands = [
        ("Проверка и установка certbot", "apt-get update -y && apt-get install -y certbot python3-certbot-nginx"),
        ("Получение и установка SSL сертификатов Let's Encrypt", 
         f"certbot --nginx -d {DOMAIN} -d www.{DOMAIN} --non-interactive --agree-tos -m {EMAIL} --redirect"),
        ("Перезапуск Nginx", "nginx -t && systemctl reload nginx"),
        ("Проверка автообновления сертификатов", "certbot renew --dry-run"),
        ("Чтение текущего Nginx конфига", "cat /etc/nginx/sites-available/socialcompass"),
    ]

    for title, cmd in commands:
        print(f"\n--- {title} ---")
        stdin, stdout, stderr = client.exec_command(cmd)
        out = stdout.read().decode('utf-8', errors='ignore')
        err = stderr.read().decode('utf-8', errors='ignore')
        if out:
            print(out.strip())
        if err and "warning" not in err.lower():
            print(f"[STDERR] {err.strip()}")

    client.close()

if __name__ == "__main__":
    run()
