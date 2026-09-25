import React, { useState, useMemo } from 'react';
import { Search, Compass } from 'lucide-react';
import PlaceCard from '../components/PlaceCard';

export default function PlacesTab({
  places,
  loading,
  favorites,
  placeType,
  onSelect,
  onToggleFav,
}) {
  const [query, setQuery] = useState('');

  const filtered = useMemo(() => {
    let result = places;

    //Фильтр по типу места
    if (placeType) {
      result = result.filter((p) => p.place_type === placeType);
    }

    //Поиск по тексту
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
  }, [places, query, placeType]);

  return (
    <>
      <div className="search-wrap" style={{ position: 'relative', marginBottom: 14 }}>
        <Search
          size={16}
          style={{
            position: 'absolute',
            left: 12,
            top: '50%',
            transform: 'translateY(-50%)',
            color: 'var(--text-soft)',
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

      <h2 className="section-title">
        {placeType ? `Тип: ${placeType}` : 'Акции и места'}{' '}
        <span className="count">{filtered.length}</span>
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
          <div className="empty-icon">
            <Compass size={36} />
          </div>
          <h3>{query || placeType ? 'Ничего не найдено' : 'Пока пусто'}</h3>
          <p>
            {query || placeType
              ? 'Попробуйте изменить фильтр или запрос'
              : 'Для этого города пока нет акций'}
          </p>
        </div>
      ) : (
        filtered.map((place) => (
          <PlaceCard
            key={place.id}
            place={place}
            isFav={favorites.some((f) => f.id === place.id)}
            onSelect={() => onSelect(place)}
            onToggleFav={() => onToggleFav(place)}
          />
        ))
      )}
    </>
  );
}