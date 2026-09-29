import sys
import paramiko

sys.stdout.reconfigure(encoding='utf-8')
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('80.90.189.13', username='root', password=r'***REMOVED***')

cmds = [
    ('user_profiles', "docker exec socialcompas_mysql mysql -ubot_user -pbot_password socialcompas_db -e 'SELECT * FROM user_profiles;'"),
    ('user_states', "docker exec socialcompas_mysql mysql -ubot_user -pbot_password socialcompas_db -e 'SELECT * FROM user_states;'"),
    ('redis keys', "docker exec socialcompas_redis redis-cli KEYS '*'"),
    ('recent app logs', "docker logs socialcompas_app --tail 40"),
]
for title, cmd in cmds:
    print(f'\n--- {title} ---')
    _, o, e = c.exec_command(cmd)
    out = o.read().decode('utf-8', errors='ignore').strip()
    if out:
        print(out)
    err = e.read().decode('utf-8', errors='ignore').strip()
    if err:
        print(f"[ERR] {err}")

c.close()
