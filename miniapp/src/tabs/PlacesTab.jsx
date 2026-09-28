import React, { useState, useMemo } from 'react';
import { Search, Compass, Map, List } from 'lucide-react';
import PlaceCard from '../components/PlaceCard';
import PlaceMap from '../components/PlaceMap';

export default function PlacesTab({
  places,
  loading,
  favorites,
  selectedTypes,
  onSelect,
  onToggleFav,
  city,
}) {
  const [query, setQuery] = useState('');
  const [viewMode, setViewMode] = useState('list'); // 'list' | 'map'

  const filtered = useMemo(() => {
    let result = places;

    // Фильтр
    if (selectedTypes && selectedTypes.length > 0) {
      result = result.filter((p) => selectedTypes.includes(p.place_type));
    }

    // Поиск по тексту
    if (query.trim()) {
      const q = query.toLowerCase();
      result = result.filter(
        (p) =>
          p.title?.toLowerCase().includes(q) ||
          p.promo_text?.toLowerCase().includes(q) ||
          p.address?.toLowerCase().includes(q)
      );
    }

    return result;
  }, [places, query, selectedTypes]);

  const headerLabel =
    selectedTypes && selectedTypes.length > 0
      ? `Типы: ${selectedTypes.join(', ')}`
      : 'Акции и места';

  return (
    <>
      <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 14 }}>
        <div className="search-wrap" style={{ position: 'relative', flex: 1, marginBottom: 0 }}>
          <Search
            size={16}
            style={{
              position: 'absolute', left: 12, top: '50%',
              transform: 'translateY(-50%)', color: 'var(--text-soft)',
            }}
          />
          <input
            className="input"
            style={{ paddingLeft: 38 }}
            placeholder="Поиск по местам и акциям"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </div>

        <div style={{ display: 'flex', background: 'var(--card-bg, #F3F4F6)', borderRadius: 10, padding: 3 }}>
          <button
            onClick={() => setViewMode('list')}
            style={{
              border: 'none',
              background: viewMode === 'list' ? 'var(--primary-color, #4F46E5)' : 'transparent',
              color: viewMode === 'list' ? '#fff' : 'var(--text-soft)',
              borderRadius: 8,
              padding: '8px 12px',
              display: 'flex',
              alignItems: 'center',
              gap: 4,
              cursor: 'pointer',
              fontSize: 13,
              fontWeight: 500,
            }}
          >
            <List size={16} /> Список
          </button>
          <button
            onClick={() => setViewMode('map')}
            style={{
              border: 'none',
              background: viewMode === 'map' ? 'var(--primary-color, #4F46E5)' : 'transparent',
              color: viewMode === 'map' ? '#fff' : 'var(--text-soft)',
              borderRadius: 8,
              padding: '8px 12px',
              display: 'flex',
              alignItems: 'center',
              gap: 4,
              cursor: 'pointer',
              fontSize: 13,
              fontWeight: 500,
            }}
          >
            <Map size={16} /> Карта
          </button>
        </div>
      </div>

      <h2 className="section-title">
        {headerLabel} <span className="count">{filtered.length}</span>
      </h2>

      {loading ? (
        Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="place-card" style={{ overflow: 'hidden' }}>
            <div className="skeleton sk-banner" />
            <div style={{ padding: 14 }}>
              <div className="skeleton sk-line sk-w60" />
              <div className="skeleton sk-line sk-w80" />
              <div className="skeleton sk-line sk-w40" />
            </div>
          </div>
        ))
      ) : filtered.length === 0 ? (
        <div className="empty">
          <div className="empty-icon"><Compass size={36} /></div>
          <h3>{query || selectedTypes?.length ? 'Ничего не найдено' : 'Пока пусто'}</h3>
          <p>
            {query || selectedTypes?.length
              ? 'Попробуйте изменить фильтр или запрос'
              : 'Для этого города пока нет акций'}
          </p>
        </div>
      ) : viewMode === 'map' ? (
        <>
          <PlaceMap
            places={filtered}
            city={city}
            onSelectPlace={onSelect}
            height="360px"
          />
          <h3 style={{ marginTop: 20, marginBottom: 12, fontSize: 15, fontWeight: 600, color: 'var(--text-main, #111827)' }}>
            Места и события на карте <span className="count">{filtered.length}</span>
          </h3>
          <div className="places-grid">
            {filtered.map((place) => (
              <PlaceCard
                key={place.id}
                place={place}
                isFav={favorites.some((f) => f.id === place.id)}
                onSelect={() => onSelect(place)}
                onToggleFav={() => onToggleFav(place)}
              />
            ))}
          </div>
        </>
      ) : (
        <div className="places-grid">
          {filtered.map((place) => (
            <PlaceCard
              key={place.id}
              place={place}
              isFav={favorites.some((f) => f.id === place.id)}
              onSelect={() => onSelect(place)}
              onToggleFav={() => onToggleFav(place)}
            />
          ))}
        </div>
      )}
    </>
  );
}