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

const extractUserFromStr = (raw) => {
  if (!raw) return null;
  try {
    const clean = raw.startsWith('#') || raw.startsWith('?') ? raw.substring(1) : raw;
    const params = new URLSearchParams(clean);
    const directId = params.get('user_id') || params.get('id');
    if (directId) return directId;

    const initDataStr = params.get('tgWebAppData') || params.get('initData') || params.get('maxWebAppData') || clean;
    if (initDataStr && initDataStr.includes('user=')) {
      const inner = new URLSearchParams(initDataStr);
      const userRaw = inner.get('user');
      if (userRaw) {
        const parsed = JSON.parse(decodeURIComponent(userRaw));
        if (parsed?.id) return String(parsed.id);
      }
    }
  } catch {}
  return null;
};

const getUserId = () => {
  try {
    // 1. Check window.location.search and hash
    const fromSearch = extractUserFromStr(window.location.search);
    if (fromSearch) {
      localStorage.setItem('sc_user_id', fromSearch);
      return fromSearch;
    }
    const fromHash = extractUserFromStr(window.location.hash);
    if (fromHash) {
      localStorage.setItem('sc_user_id', fromHash);
      return fromHash;
    }

    // 2. Telegram / MAX WebApp SDK objects
    const tgId = window.Telegram?.WebApp?.initDataUnsafe?.user?.id;
    if (tgId) {
      localStorage.setItem('sc_user_id', String(tgId));
      return String(tgId);
    }
    const tgInitData = window.Telegram?.WebApp?.initData;
    if (tgInitData) {
      const parsedFromInit = extractUserFromStr(tgInitData);
      if (parsedFromInit) {
        localStorage.setItem('sc_user_id', parsedFromInit);
        return parsedFromInit;
      }
    }

    // 3. MAX Messenger globals
    const maxId = window.MaxWebApp?.user?.id || window.Max?.user?.id || window.MAX?.user?.id;
    if (maxId) {
      localStorage.setItem('sc_user_id', String(maxId));
      return String(maxId);
    }

    // 4. Saved in localStorage
    const saved = localStorage.getItem('sc_user_id');
    if (saved) return saved;
  } catch {}
  return 'miniapp_user_1';
};

const USER_ID = getUserId();

export default function App() {
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
  }, [city, category, isSurveyDone]);

  useEffect(() => {
    fetchProfile(USER_ID).then((p) => {
      if (p?.city && p?.category) {
        setCity(p.city);
        setCategory(p.category);
        localStorage.setItem('sc_city', p.city);
        localStorage.setItem('sc_category', p.category);
        localStorage.setItem('sc_survey_done', 'true');
        setIsSurveyDone(true);
      }
    }).catch(() => {});
  }, []);

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
      const data = await fetchFavorites(USER_ID);
      setFavorites(data.items || []);
    } catch (e) {
      console.error(e);
    }
  };

  const handleToggleFavorite = async (place) => {
    const isFav = favorites.some((f) => f.id === place.id);
    try {
      if (isFav) {
        await removeFavorite(USER_ID, place.id);
      } else {
        await addFavorite(USER_ID, place.id);
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
    setCity(newCity);
    setCategory(newCategory);
    setSelectedTypes([]);
    localStorage.setItem('sc_city', newCity);
    localStorage.setItem('sc_category', newCategory);
    localStorage.setItem('sc_survey_done', 'true');
    setIsSurveyDone(true);
    setIsEditMode(false);
    try {
      await saveProfile(USER_ID, newCity, newCategory);
      showToast('Профиль сохранён');
    } catch (e) {
      console.error(e);
    }
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