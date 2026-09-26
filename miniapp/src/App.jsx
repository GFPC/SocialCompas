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

const USER_ID = 'miniapp_user_1';

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

  // Множественный фильтр по типам
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
    // eslint-disable-next-line
  }, [city, category, isSurveyDone]);

  useEffect(() => {
    if (isSurveyDone) {
      fetchProfile(USER_ID).then((p) => {
        if (p?.city && p?.category) {
          setCity(p.city);
          setCategory(p.category);
        }
      }).catch(() => {});
    }
    // eslint-disable-next-line
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
      showToast('Убрано из избранного');
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

  // === Фильтр ===
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
            {activeTab === 'chat' && <ChatTab />}
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