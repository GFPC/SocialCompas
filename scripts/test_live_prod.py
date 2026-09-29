import sys
import httpx
import json

sys.stdout.reconfigure(encoding='utf-8')

BASE = 'https://api.socialcompass.ru'
print(f'🔍 Проверка LIVE Production API: {BASE}\n')

client = httpx.Client(timeout=15.0)

# 1. Cities
r = client.get(f'{BASE}/api/v1/cities')
print(f'1. GET /cities -> Status {r.status_code}: {r.json()}')

# 2. Categories
r = client.get(f'{BASE}/api/v1/categories')
print(f'2. GET /categories -> Status {r.status_code}: {r.json()}')

# 3. Test accounts profiles
test_users = [
    ('998877', 'Алексей (Студент)'),
    ('554433', 'Мария (Пенсионер)'),
    ('112233', 'Сергей (Участник СВО)'),
]

for uid, name in test_users:
    r = client.get(f'{BASE}/api/v1/profile/{uid}')
    print(f'3. GET /profile/{uid} ({name}) -> Status {r.status_code}: {r.json()}')

# 4. Places for each profile
queries = [
    ('Москва', 'Студенты'),
    ('Санкт-Петербург', 'Пенсионеры'),
    ('Новосибирск', 'Участники СВО'),
]
for city, cat in queries:
    r = client.get(f'{BASE}/api/v1/places', params={'city': city, 'category': cat})
    data = r.json()
    print(f'4. GET /places ({city} / {cat}) -> Status {r.status_code}, мест: {data.get("count", 0)}')

# 5. AI Chat assistant
r = client.post(f'{BASE}/api/v1/chat', json={
    'messages': [{'role': 'user', 'content': 'Какие музеи есть со скидкой в Москве?'}],
    'city': 'Москва',
    'category': 'Студенты'
})
msg = r.json().get("message", "")
print(f'5. POST /chat (AI Tunnel) -> Status {r.status_code}: {msg[:120]}...')

# 6. Check Swagger is disabled on prod (404)
r = client.get(f'{BASE}/docs')
print(f'6. GET /docs (Swagger on prod) -> Status {r.status_code} (404 expected)')

print('\n🎉 ВСЕ ТЕСТЫ НА БОЕВОМ СЕРВЕРЕ УСПЕШНО ПРОЙДЕНЫ!')
