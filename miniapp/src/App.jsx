import React, { useState, useEffect } from 'react';
import { Compass, Heart, Settings, MapPin, ExternalLink, Bookmark, Check, User } from 'lucide-react';
import { fetchPlaces, fetchFavorites, addFavorite, removeFavorite, saveProfile } from './api';

const USER_ID = 'miniapp_user_1';

export default function App() {
  const [activeTab, setActiveTab] = useState('places');
  const [city, setCity] = useState(localStorage.getItem('sc_city') || 'Москва');
  const [category, setCategory] = useState(localStorage.getItem('sc_category') || 'Студенты');
  const [isSurveyDone, setIsSurveyDone] = useState(Boolean(localStorage.getItem('sc_survey_done')));

  const [places, setPlaces] = useState([]);
  const [favorites, setFavorites] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedPlace, setSelectedPlace] = useState(null);

  // Load places and favorites when city or category changes
  useEffect(() => {
    if (isSurveyDone) {
      loadPlaces();
      loadFavorites();
    }
  }, [city, category, isSurveyDone]);

  const loadPlaces = async () => {
    setLoading(true);
    try {
      const data = await fetchPlaces(city, category);
      setPlaces(data.items || []);
    } catch (e) {
      console.error(e);
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
        setFavorites((prev) => prev.filter((f) => f.id !== place.id));
      } else {
        await addFavorite(USER_ID, place.id);
        setFavorites((prev) => [...prev, place]);
      }
    } catch (e) {
      alert('Ошибка при обновлении избранного');
    }
  };

  const handleFinishSurvey = async (newCity, newCategory) => {
    setCity(newCity);
    setCategory(newCategory);
    localStorage.setItem('sc_city', newCity);
    localStorage.setItem('sc_category', newCategory);
    localStorage.setItem('sc_survey_done', 'true');
    setIsSurveyDone(true);
    try {
      await saveProfile(USER_ID, newCity, newCategory);
    } catch (e) {
      console.error(e);
    }
  };

  // Survey View
  if (!isSurveyDone) {
    return <SurveyView onComplete={handleFinishSurvey} initialCity={city} initialCategory={category} />;
  }

  return (
    <div className="app-container">
      {/* Header */}
      <div className="header">
        <h1>
          <Compass size={22} /> Социальный Компас
        </h1>
        <p>{city} • {category}</p>
      </div>

      {/* Main Content */}
      <div className="content">
        {selectedPlace ? (
          <PlaceDetailView
            place={selectedPlace}
            isFav={favorites.some((f) => f.id === selectedPlace.id)}
            onToggleFav={() => handleToggleFavorite(selectedPlace)}
            onBack={() => setSelectedPlace(null)}
          />
        ) : (
          <>
            {activeTab === 'places' && (
              <div>
                <h2 style={{ fontSize: '18px', fontWeight: 700, marginBottom: '12px' }}>
                  Акции и интересные места ({places.length})
                </h2>
                {loading ? (
                  <p style={{ textAlign: 'center', padding: '20px', color: '#64748b' }}>Загрузка мест...</p>
                ) : places.length === 0 ? (
                  <div className="card" style={{ textAlign: 'center', padding: '30px' }}>
                    <p>Для выбранного города и категории пока нет акций.</p>
                  </div>
                ) : (
                  places.map((place) => (
                    <PlaceCard
                      key={place.id}
                      place={place}
                      isFav={favorites.some((f) => f.id === place.id)}
                      onSelect={() => setSelectedPlace(place)}
                      onToggleFav={() => handleToggleFavorite(place)}
                    />
                  ))
                )}
              </div>
            )}

            {activeTab === 'favorites' && (
              <div>
                <h2 style={{ fontSize: '18px', fontWeight: 700, marginBottom: '12px' }}>
                  Избранные места ({favorites.length})
                </h2>
                {favorites.length === 0 ? (
                  <div className="card" style={{ textAlign: 'center', padding: '30px' }}>
                    <p>У вас пока нет сохраненных мест.</p>
                  </div>
                ) : (
                  favorites.map((place) => (
                    <PlaceCard
                      key={place.id}
                      place={place}
                      isFav={true}
                      onSelect={() => setSelectedPlace(place)}
                      onToggleFav={() => handleToggleFavorite(place)}
                    />
                  ))
                )}
              </div>
            )}

            {activeTab === 'settings' && (
              <div>
                <h2 style={{ fontSize: '18px', fontWeight: 700, marginBottom: '12px' }}>Настройки профиля</h2>
                <div className="card">
                  <p style={{ marginBottom: '8px' }}><strong>Город:</strong> {city}</p>
                  <p style={{ marginBottom: '16px' }}><strong>Категория:</strong> {category}</p>
                  <button
                    className="btn btn-primary"
                    onClick={() => setIsSurveyDone(false)}
                  >
                    ✏️ Изменить данные профиля
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {/* Bottom Navigation */}
      <div className="bottom-nav">
        <button
          className={`nav-item ${activeTab === 'places' ? 'active' : ''}`}
          onClick={() => { setActiveTab('places'); setSelectedPlace(null); }}
        >
          <Compass size={20} />
          <span>Места</span>
        </button>
        <button
          className={`nav-item ${activeTab === 'favorites' ? 'active' : ''}`}
          onClick={() => { setActiveTab('favorites'); setSelectedPlace(null); }}
        >
          <Heart size={20} />
          <span>Избранное</span>
        </button>
        <button
          className={`nav-item ${activeTab === 'settings' ? 'active' : ''}`}
          onClick={() => { setActiveTab('settings'); setSelectedPlace(null); }}
        >
          <Settings size={20} />
          <span>Настройки</span>
        </button>
      </div>
    </div>
  );
}

function PlaceCard({ place, isFav, onSelect, onToggleFav }) {
  return (
    <div className="card">
      <span className="badge">{place.place_type || 'Место'}</span>
      <div className="place-title" onClick={onSelect} style={{ cursor: 'pointer' }}>
        {place.title}
      </div>
      {place.promo_text && <div className="place-promo">{place.promo_text}</div>}
      {place.address && (
        <div className="place-address">
          <MapPin size={14} /> {place.address}
        </div>
      )}
      <div style={{ display: 'flex', gap: '8px', marginTop: '12px' }}>
        <button className="btn btn-secondary" style={{ flex: 1 }} onClick={onSelect}>
          Подробнее
        </button>
        <button
          className={`btn ${isFav ? 'btn-primary' : 'btn-outline'}`}
          style={{ width: '48px', padding: 0 }}
          onClick={onToggleFav}
        >
          <Bookmark size={18} fill={isFav ? 'currentColor' : 'none'} />
        </button>
      </div>
    </div>
  );
}

function PlaceDetailView({ place, isFav, onToggleFav, onBack }) {
  return (
    <div>
      <button className="btn btn-outline" style={{ marginBottom: '16px', width: 'auto' }} onClick={onBack}>
        ← Назад к списку
      </button>

      <div className="card">
        <span className="badge">{place.place_type || 'Место'}</span>
        <h2 style={{ fontSize: '20px', fontWeight: 700, marginBottom: '12px' }}>{place.title}</h2>

        {place.promo_text && (
          <div style={{ background: '#eff6ff', padding: '12px', borderRadius: '8px', marginBottom: '12px' }}>
            <strong>🏷 Промоакция:</strong>
            <p style={{ marginTop: '4px', fontSize: '14px' }}>{place.promo_text}</p>
          </div>
        )}

        {place.schedule && (
          <p style={{ fontSize: '13px', color: '#475569', marginBottom: '8px' }}>
            <strong>⏰ Время работы:</strong> {place.schedule}
          </p>
        )}

        {place.address && (
          <p style={{ fontSize: '13px', color: '#475569', marginBottom: '16px' }}>
            <strong>📍 Адрес:</strong> {place.address}
          </p>
        )}

        <p style={{ fontSize: '12px', color: '#94a3b8', fontStyle: 'italic', marginBottom: '16px' }}>
          *Скидки и льготы предоставляются при предъявлении документа.
        </p>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <button className={`btn ${isFav ? 'btn-secondary' : 'btn-primary'}`} onClick={onToggleFav}>
            <Bookmark size={18} fill={isFav ? 'currentColor' : 'none'} />
            {isFav ? 'Удалить из избранного' : 'Добавить в избранное'}
          </button>
          {place.map_url && (
            <a href={place.map_url} target="_blank" rel="noreferrer" style={{ textDecoration: 'none' }}>
              <button className="btn btn-outline">
                <ExternalLink size={18} /> Посмотреть на карте / сайте
              </button>
            </a>
          )}
        </div>
      </div>
    </div>
  );
}

function SurveyView({ onComplete, initialCity, initialCategory }) {
  const [step, setStep] = useState(1);
  const [selectedCity, setSelectedCity] = useState(initialCity);
  const [selectedCategory, setSelectedCategory] = useState(initialCategory);

  const cities = ['Москва', 'Новосибирск'];
  const categories = ['Студенты', 'Пенсионеры', 'Участники СВО'];

  return (
    <div className="app-container" style={{ justifyContent: 'center', padding: '20px' }}>
      <div className="survey-box">
        <Compass size={48} color="#2563eb" style={{ marginBottom: '12px' }} />
        <h2 className="survey-title">Добро пожаловать в «Социальный Компас»</h2>
        <p style={{ fontSize: '14px', color: '#64748b', marginBottom: '20px' }}>
          Пройдите короткий опрос, чтобы найти лучшие скидки и места в вашем городе.
        </p>

        {step === 1 ? (
          <div>
            <h3 style={{ fontSize: '15px', fontWeight: 600 }}>Выберите ваш город:</h3>
            <div className="options-grid">
              {cities.map((c) => (
                <div
                  key={c}
                  className={`option-btn ${selectedCity === c ? 'selected' : ''}`}
                  onClick={() => setSelectedCity(c)}
                >
                  <span>{c}</span>
                  {selectedCity === c && <Check size={18} />}
                </div>
              ))}
            </div>
            <button
              className="btn btn-primary"
              style={{ marginTop: '20px' }}
              onClick={() => setStep(2)}
            >
              Далее →
            </button>
          </div>
        ) : (
          <div>
            <h3 style={{ fontSize: '15px', fontWeight: 600 }}>Выберите вашу категорию:</h3>
            <div className="options-grid">
              {categories.map((cat) => (
                <div
                  key={cat}
                  className={`option-btn ${selectedCategory === cat ? 'selected' : ''}`}
                  onClick={() => setSelectedCategory(cat)}
                >
                  <span>{cat}</span>
                  {selectedCategory === cat && <Check size={18} />}
                </div>
              ))}
            </div>
            <div style={{ display: 'flex', gap: '8px', marginTop: '20px' }}>
              <button className="btn btn-secondary" onClick={() => setStep(1)}>
                ← Назад
              </button>
              <button
                className="btn btn-primary"
                onClick={() => onComplete(selectedCity, selectedCategory)}
              >
                Завершить
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
