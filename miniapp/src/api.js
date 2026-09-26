const API_BASE = import.meta.env.VITE_API_URL || 'https://api.socialcompass.ru';


export async function fetchPlaces(city, category) {
  const params = new URLSearchParams({ city, category });
  const res = await fetch(`${API_BASE}/api/v1/places?${params}`);
  if (!res.ok) throw new Error('Ошибка загрузки списка мест');
  const data = await res.json();
  console.log('[fetchPlaces]', city, category, '→', data.count, 'мест');
  return data;
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