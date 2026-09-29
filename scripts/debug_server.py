import sys
import paramiko

sys.stdout.reconfigure(encoding='utf-8')
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('80.90.189.13', username='root', password=r'***REMOVED***')

cmds = [
    ('curl /api/v1/profile/445041610', 
     "docker exec socialcompas_app curl -s http://127.0.0.1:8000/api/v1/profile/445041610"),
    ('user_profiles table', 
     "docker exec socialcompas_mysql mysql -ubot_user -pbot_password socialcompas_db -e 'SELECT * FROM user_profiles;'"),
    ('redis fsm for 445041610',
     "docker exec socialcompas_redis redis-cli GET 'fsm:data:445041610'"),
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
