const API_BASE = import.meta.env.VITE_API_URL || 'https://api.socialcompass.ru';


// МОК-ДАННЫЕ (только для разработки UI)
// Удалить, когда бэкенд зальёт реальные места в БД.

const MOCK_PLACES = [
  {
    id: 1,
    title: 'Аполло. День студента',
    place_type: 'Боулинг',
    category: 'Студенты',
    promo_text: 'Забудьте о парах и экзаменах хотя бы ненадолго! Хватайте друзей и мититесь в боулинг с нашей крутой акцией: каждый будний день с 12:00 до 16:00 — всего за 300₽.',
    address: 'ул. Пермитина, 24, этаж 2',
    schedule: 'Пн–Пт 12:00–16:00',
    map_url: 'https://yandex.ru/maps/',
  },
  {
    id: 2,
    title: 'СинеМА Парк. Студенты скидка 20%',
    place_type: 'Кинотеатр',
    category: 'Студенты',
    promo_text: 'Предложение для всех на каждый день: -50% детям, -30% пенсионерам, -20% учащимся.',
    address: 'Красный проспект, 101',
    schedule: 'Ежедневно 10:00–23:00',
    map_url: 'https://yandex.ru/maps/',
  },
  {
    id: 3,
    title: 'Играй студент в бильярд SkyCity со скидкой 50%',
    place_type: 'Бильярд',
    category: 'Студенты',
    promo_text: 'Скидка 50% на все столы по студенческому билету.',
    address: 'ул. Ленина, 12',
    schedule: 'Ежедневно 12:00–02:00',
    map_url: 'https://yandex.ru/maps/',
  },
  {
    id: 4,
    title: 'Кофейня «Точка» — кофе за 99₽',
    place_type: 'Кафе',
    category: 'Студенты',
    promo_text: 'Любой кофе навынос за 99₽ по студенческому.',
    address: 'ул. Пирогова, 8',
    schedule: 'Пн–Пт 8:00–22:00',
  },
  {
    id: 5,
    title: 'Бассейн «Нептун» — скидка 40%',
    place_type: 'Спорт',
    category: 'Студенты',
    promo_text: 'Посещение бассейна со скидкой 40% для студентов.',
    address: 'ул. Спортивная, 5',
    schedule: 'Ежедневно 7:00–23:00',
  },
];


export async function fetchPlaces(city, category) {
  try {
    const params = new URLSearchParams({ city, category });
    const res = await fetch(`${API_BASE}/api/v1/places?${params}`);
    if (!res.ok) throw new Error('Ошибка загрузки списка мест');
    const data = await res.json();

    if (!data.items || data.items.length === 0) {
      console.warn('[fetchPlaces] API пуст, отдаю мок-данные');
      return { items: MOCK_PLACES };
    }
    return data;
  } catch (e) {
    console.warn('[fetchPlaces] Ошибка API, отдаю мок-данные', e);
    return { items: MOCK_PLACES };
  }
}

export async function fetchPlaceDetail(placeId) {
  const res = await fetch(`${API_BASE}/api/v1/places/${placeId}`);
  if (!res.ok) throw new Error('Ошибка загрузки информации о месте');
  return await res.json();
}

// избранное

export async function fetchFavorites(userId) {
  try {
    const res = await fetch(`${API_BASE}/api/v1/favorites/${userId}`);
    if (!res.ok) {
      if (res.status === 404) return { items: [] };
      throw new Error('Ошибка загрузки избранного');
    }
    const data = await res.json();
    const items = Array.isArray(data) ? data : data.items || [];
    return { items };
  } catch (e) {
    console.warn('[fetchFavorites] fallback to empty', e);
    return { items: [] };
  }
}

export async function addFavorite(userId, placeId) {
  const res = await fetch(`${API_BASE}/api/v1/favorites/${userId}/${placeId}`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error('Ошибка добавления в избранное');
  return await res.json();
}

export async function removeFavorite(userId, placeId) {
  const res = await fetch(`${API_BASE}/api/v1/favorites/${userId}/${placeId}`, {
    method: 'DELETE',
  });
  if (!res.ok) throw new Error('Ошибка удаления из избранного');
  return await res.json();
}

// профиль
export async function fetchProfile(userId) {
  try {
    const res = await fetch(`${API_BASE}/api/v1/profile/${userId}`);
    if (!res.ok) return null;
    const data = await res.json();
    return data.profile || data;
  } catch {
    return null;
  }
}

export async function saveProfile(userId, city, category) {
  try {
    const res = await fetch(`${API_BASE}/api/v1/profile`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId, city, category }),
    });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

// Временно, пока нет реальных данных!!!

const LISTS_KEY = (userId) => `sc_lists_${userId}`;

function readLists(userId) {
  try {
    return JSON.parse(localStorage.getItem(LISTS_KEY(userId)) || '[]');
  } catch {
    return [];
  }
}

function writeLists(userId, lists) {
  localStorage.setItem(LISTS_KEY(userId), JSON.stringify(lists));
}

export function getLists(userId) {
  return readLists(userId);
}

export function createList(userId, name, emoji = '📌') {
  const lists = readLists(userId);
  const list = {
    id: 'list_' + Date.now() + '_' + Math.random().toString(36).slice(2, 6),
    name,
    emoji,
    place_ids: [],
    created_at: new Date().toISOString(),
  };
  lists.push(list);
  writeLists(userId, lists);
  return list;
}

export function deleteList(userId, listId) {
  const lists = readLists(userId).filter((l) => l.id !== listId);
  writeLists(userId, lists);
  return lists;
}

export function addPlaceToList(userId, listId, place) {
  const lists = readLists(userId);
  const list = lists.find((l) => l.id === listId);
  if (!list) return lists;
  if (!list.place_ids.some((p) => p.id === place.id)) {
    list.place_ids.push(place);
  }
  writeLists(userId, lists);
  return lists;
}

export function removePlaceFromList(userId, listId, placeId) {
  const lists = readLists(userId);
  const list = lists.find((l) => l.id === listId);
  if (!list) return lists;
  list.place_ids = list.place_ids.filter((p) => p.id !== placeId);
  writeLists(userId, lists);
  return lists;
}

export function isPlaceInList(userId, listId, placeId) {
  const list = readLists(userId).find((l) => l.id === listId);
  return Boolean(list?.place_ids.some((p) => p.id === placeId));
}