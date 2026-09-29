import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  fetchPlaces, fetchFavorites, addFavorite, removeFavorite,
  saveProfile, fetchProfile,
} from './api';

import TopBar from './components/TopBar';
import BottomNav from './components/BottomNav';
import Toast from './components/Toast';
import SurveyView from './components/SurveyView';
import PlaceDetail from './components/PlaceDetail';
import FilterSheet from './components/FilterSheet';

import PlacesTab from './tabs/PlacesTab';
import ChatTab from './tabs/ChatTab';
import FavoritesTab from './tabs/FavoritesTab';
import ProfileTab from './tabs/ProfileTab';

const parseInitDataUserId = (raw) => {
  if (!raw) return null;
  try {
    const userRaw = new URLSearchParams(raw).get('user');
    if (userRaw) {
      const parsed = JSON.parse(userRaw);
      if (parsed?.id) return String(parsed.id);
    }
  } catch {}
  return null;
};

// MAX кладёт данные пользователя в window.WebApp.initData / initDataUnsafe.user.id —
// это тот же id, что и в боте. Всё остальное — запасные варианты для браузера/отладки.
const getUserId = () => {
  try {
    const webApp = window.WebApp;
    const id =
      webApp?.initDataUnsafe?.user?.id ||
      parseInitDataUserId(webApp?.initData) ||
      parseInitDataUserId(window.Telegram?.WebApp?.initData);
    if (id) {
      localStorage.setItem('sc_user_id', String(id));
      return String(id);
    }

    const hashParams = new URLSearchParams((window.location.hash || '').replace(/^#/, ''));
    const fromUrl =
      new URLSearchParams(window.location.search).get('user_id') ||
      hashParams.get('user_id') ||
      parseInitDataUserId(hashParams.get('WebAppData') || hashParams.get('tgWebAppData'));
    if (fromUrl) {
      localStorage.setItem('sc_user_id', fromUrl);
      return fromUrl;
    }

    const saved = localStorage.getItem('sc_user_id');
    if (saved) return saved;

    // Открыто вне MAX (обычный браузер): локальный гостевой id, без синхронизации с ботом
    const guest = 'guest_' + Math.random().toString(36).slice(2, 12);
    localStorage.setItem('sc_user_id', guest);
    return guest;
  } catch {}
  return 'guest_local';
};

export default function App() {
  const [userId, setUserId] = useState(() => getUserId());
  const [activeTab, setActiveTab] = useState('places');
  const [city, setCity] = useState(localStorage.getItem('sc_city') || 'Москва');
  const [category, setCategory] = useState(localStorage.getItem('sc_category') || 'Студенты');
  const [isSurveyDone, setIsSurveyDone] = useState(Boolean(localStorage.getItem('sc_survey_done')));
  const [isEditMode, setIsEditMode] = useState(false);

  const [places, setPlaces] = useState([]);
  const [favorites, setFavorites] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedPlace, setSelectedPlace] = useState(null);

  // Фильтр
  const [selectedTypes, setSelectedTypes] = useState([]);
  const [filterOpen, setFilterOpen] = useState(false);

  const [toasts, setToasts] = useState([]);

  const showToast = useCallback((message) => {
    const id = Date.now() + Math.random();
    setToasts((prev) => [...prev, { id, message }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 2400);
  }, []);

  const placeTypes = useMemo(() => {
    const set = new Set();
    places.forEach((p) => { if (p.place_type) set.add(p.place_type); });
    return Array.from(set).sort();
  }, [places]);

  useEffect(() => {
    if (isSurveyDone) {
      loadPlaces();
      loadFavorites();
    }
  }, [city, category, isSurveyDone, userId]);

  // Профиль на сервере — источник правды: подтягиваем при старте, при возврате в приложение
  // и периодически, чтобы изменения из бота появлялись без перезапуска.
  const syncProfile = useCallback(async (uid) => {
    const p = await fetchProfile(uid);
    if (p === undefined) return; // сеть/сервер недоступны — оставляем локальное состояние
    if (p?.city && p?.category) {
      setCity((c) => (c === p.city ? c : p.city));
      setCategory((c) => (c === p.category ? c : p.category));
      localStorage.setItem('sc_city', p.city);
      localStorage.setItem('sc_category', p.category);
      localStorage.setItem('sc_survey_done', 'true');
      setIsSurveyDone(true);
    } else {
      // у этого пользователя ещё нет профиля — показываем опрос
      localStorage.removeItem('sc_survey_done');
      setIsSurveyDone(false);
    }
  }, []);

  useEffect(() => {
    try {
      window.WebApp?.ready?.();
    } catch {}
    const activeUid = getUserId();
    if (activeUid !== userId) setUserId(activeUid);
    syncProfile(activeUid);
  }, []);

  useEffect(() => {
    if (!userId || isEditMode) return undefined;
    const refresh = () => {
      if (document.visibilityState === 'visible') {
        syncProfile(userId);
        loadFavorites();
      }
    };
    document.addEventListener('visibilitychange', refresh);
    window.addEventListener('focus', refresh);
    const timer = setInterval(refresh, 20000);
    return () => {
      document.removeEventListener('visibilitychange', refresh);
      window.removeEventListener('focus', refresh);
      clearInterval(timer);
    };
  }, [userId, isEditMode, syncProfile]);

  const loadPlaces = async () => {
    setLoading(true);
    try {
      const data = await fetchPlaces(city, category);
      setPlaces(data.items || []);
    } catch (e) {
      console.error(e);
      showToast('Не удалось загрузить места');
    } finally {
      setLoading(false);
    }
  };

  const loadFavorites = async () => {
    try {
      const activeUid = userId || getUserId();
      const data = await fetchFavorites(activeUid);
      setFavorites(data.items || []);
    } catch (e) {
      console.error(e);
    }
  };

  const handleToggleFavorite = async (place) => {
    const isFav = favorites.some((f) => f.id === place.id);
    const activeUid = userId || getUserId();
    try {
      if (isFav) {
        await removeFavorite(activeUid, place.id);
      } else {
        await addFavorite(activeUid, place.id);
      }
    } catch (e) {
      console.warn('API ошибка, обновляю локально', e);
    }
    if (isFav) {
      setFavorites((prev) => prev.filter((f) => f.id !== place.id));
      showToast('Удаленно');
    } else {
      setFavorites((prev) => [...prev, place]);
      showToast('Добавлено в избранное');
    }
  };

  const handleRemoveFavorite = (place) => handleToggleFavorite(place);

  const handleFinishSurvey = async (newCity, newCategory) => {
    const activeUid = getUserId();
    setUserId(activeUid);
    setCity(newCity);
    setCategory(newCategory);
    setSelectedTypes([]);
    localStorage.setItem('sc_city', newCity);
    localStorage.setItem('sc_category', newCategory);
    localStorage.setItem('sc_survey_done', 'true');
    setIsSurveyDone(true);
    setIsEditMode(false);
    const saved = await saveProfile(activeUid, newCity, newCategory);
    showToast(saved ? 'Профиль сохранён' : 'Не удалось синхронизировать с ботом');
  };

  // Фильтр
  const toggleType = (type) => {
    setSelectedTypes((prev) =>
      prev.includes(type)
        ? prev.filter((t) => t !== type)
        : [...prev, type]
    );
  };

  const clearTypes = () => setSelectedTypes([]);

  if (!isSurveyDone || isEditMode) {
    return (
      <SurveyView
        onComplete={handleFinishSurvey}
        initialCity={city}
        initialCategory={category}
        isEdit={isEditMode}
      />
    );
  }

  return (
    <div className="app-container">
      <TopBar
        city={city}
        selectedTypes={selectedTypes}
        onFilterClick={() => setFilterOpen(true)}
        onClearFilter={clearTypes}
      />

      <main className="content">
        {selectedPlace ? (
          <PlaceDetail
            place={selectedPlace}
            isFav={favorites.some((f) => f.id === selectedPlace.id)}
            onToggleFav={() => handleToggleFavorite(selectedPlace)}
            onBack={() => setSelectedPlace(null)}
          />
        ) : (
          <>
            {activeTab === 'places' && (
              <PlacesTab
                places={places}
                loading={loading}
                favorites={favorites}
                selectedTypes={selectedTypes}
                onSelect={setSelectedPlace}
                onToggleFav={handleToggleFavorite}
                city={city}
              />
            )}
            {activeTab === 'favorites' && (
              <FavoritesTab
                favorites={favorites}
                selectedTypes={selectedTypes}
                onSelect={setSelectedPlace}
                onToggleFav={handleToggleFavorite}
                onRemove={handleRemoveFavorite}
              />
            )}
            {activeTab === 'chat' && <ChatTab city={city} category={category} />}
            {activeTab === 'profile' && (
              <ProfileTab
                city={city}
                category={category}
                onEdit={() => setIsEditMode(true)}
              />
            )}
          </>
        )}
      </main>

      <BottomNav
        active={activeTab}
        onChange={(tab) => { setActiveTab(tab); setSelectedPlace(null); }}
        favoritesCount={favorites.length}
      />

      {filterOpen && (
        <FilterSheet
          types={placeTypes}
          selected={selectedTypes}
          onToggle={toggleType}
          onClear={clearTypes}
          onClose={() => setFilterOpen(false)}
        />
      )}

      <Toast toasts={toasts} />
    </div>
  );
}