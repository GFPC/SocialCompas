import { getInitData } from './utils/maxBridge';

// Пустая строка в VITE_API_URL = тот же origin (Docker-сборка, где API отдаёт и MiniApp).
// Не задана вовсе = боевой API.
const API_BASE = import.meta.env.VITE_API_URL ?? 'https://api.socialcompass.ru';

// ─── Авторизация ────────────────────────────────────────────────────────────
// Внутри MAX приложение получает подписанный initData; сервер проверяет подпись (HMAC от токена бота)
// и выдаёт токен, привязанный к user.id. Вне MAX используется анонимный guest_* id без токена.

export const isGuestId = (userId) => String(userId).startsWith('guest_');

let cachedToken = null;
let cachedTokenUser = null;
let tokenRequest = null;

async function requestToken() {
  const initData = getInitData();
  if (!initData) throw new Error('Нет initData: приложение открыто вне MAX');
  const res = await fetch(`${API_BASE}/api/v1/auth/webapp`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ init_data: initData }),
  });
  if (!res.ok) throw new Error('Не удалось подтвердить пользователя MAX');
  const data = await res.json();
  cachedToken = data.token;
  cachedTokenUser = String(data.user_id);
  return cachedToken;
}

async function getToken(userId, { force = false } = {}) {
  if (isGuestId(userId)) return null;
  if (!force && cachedToken && cachedTokenUser === String(userId)) return cachedToken;
  if (!tokenRequest) {
    tokenRequest = requestToken().finally(() => {
      tokenRequest = null;
    });
  }
  return tokenRequest;
}

/** fetch с Bearer-токеном пользователя; при 401 один раз обновляет токен и повторяет запрос. */
async function authFetch(userId, url, options = {}) {
  const send = async (force) => {
    const token = await getToken(userId, { force });
    const headers = { ...(options.headers || {}) };
    if (token) headers.Authorization = `Bearer ${token}`;
    return fetch(url, { ...options, headers });
  };
  let res = await send(false);
  if (res.status === 401 && !isGuestId(userId)) res = await send(true);
  return res;
}

const userUrl = (path, userId) => `${API_BASE}/api/v1/${path}/${encodeURIComponent(userId)}`;

export async function fetchPlaces(city, category) {
  const params = new URLSearchParams({ city, category });
  const res = await fetch(`${API_BASE}/api/v1/places?${params}`);
  if (!res.ok) throw new Error('Ошибка загрузки списка мест');
  return await res.json();
}

export async function fetchPlaceDetail(placeId) {
  const res = await fetch(`${API_BASE}/api/v1/places/${placeId}`);
  if (!res.ok) throw new Error('Ошибка загрузки информации о месте');
  return await res.json();
}

// избранное: ошибки пробрасываются наверх, чтобы UI не показывал ложный успех
export async function fetchFavorites(userId) {
  const res = await authFetch(userId, userUrl('favorites', userId));
  if (res.status === 404) return { items: [] };
  if (!res.ok) throw new Error('Ошибка загрузки избранного');
  const data = await res.json();
  return { items: Array.isArray(data) ? data : data.items || [] };
}

export async function addFavorite(userId, placeId) {
  const res = await authFetch(userId, `${userUrl('favorites', userId)}/${placeId}`, { method: 'POST' });
  if (!res.ok) throw new Error('Ошибка добавления в избранное');
  return await res.json();
}

export async function removeFavorite(userId, placeId) {
  const res = await authFetch(userId, `${userUrl('favorites', userId)}/${placeId}`, { method: 'DELETE' });
  if (!res.ok) throw new Error('Ошибка удаления из избранного');
  return await res.json();
}

// профиль: undefined — сервер/сеть недоступны, null — у пользователя ещё нет профиля
export async function fetchProfile(userId) {
  try {
    const res = await authFetch(userId, userUrl('profile', userId));
    if (!res.ok) return undefined;
    const data = await res.json();
    return data.profile ?? null;
  } catch {
    return undefined;
  }
}

export async function saveProfile(userId, city, category) {
  try {
    const res = await authFetch(userId, `${API_BASE}/api/v1/profile`, {
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

// ИИ Чат (AI Tunnel API)
export async function sendChatMessage(messages, city = 'Москва', category = 'Студенты') {
  const formattedMessages = messages.map((m) => ({
    role: m.role === 'ai' ? 'assistant' : m.role,
    content: m.text || m.content,
  }));

  const res = await fetch(`${API_BASE}/api/v1/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      messages: formattedMessages,
      city,
      category,
    }),
  });

  if (!res.ok) {
    if (res.status === 429) {
      throw new Error('Превышен лимит запросов к ИИ (10 в минуту). Подождите немного.');
    }
    throw new Error('Ошибка взаимодействия с ИИ-сервисом');
  }

  const data = await res.json();
  return data.message;
}

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