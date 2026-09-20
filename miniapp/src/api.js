const API_BASE = import.meta.env.VITE_API_URL || '';

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

export async function fetchFavorites(userId) {
  const res = await fetch(`${API_BASE}/api/v1/favorites/${userId}`);
  if (!res.ok) throw new Error('Ошибка загрузки избранного');
  return await res.json();
}

export async function addFavorite(userId, placeId) {
  const res = await fetch(`${API_BASE}/api/v1/favorites/${userId}/${placeId}`, { method: 'POST' });
  if (!res.ok) throw new Error('Ошибка добавления в избранное');
  return await res.json();
}

export async function removeFavorite(userId, placeId) {
  const res = await fetch(`${API_BASE}/api/v1/favorites/${userId}/${placeId}`, { method: 'DELETE' });
  if (!res.ok) throw new Error('Ошибка удаления из избранного');
  return await res.json();
}

export async function fetchProfile(userId) {
  const res = await fetch(`${API_BASE}/api/v1/profile/${userId}`);
  if (!res.ok) return null;
  const data = await res.json();
  return data.profile;
}

export async function saveProfile(userId, city, category) {
  const res = await fetch(`${API_BASE}/api/v1/profile`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: userId, city, category })
  });
  if (!res.ok) throw new Error('Ошибка сохранения профиля');
  return await res.json();
}
