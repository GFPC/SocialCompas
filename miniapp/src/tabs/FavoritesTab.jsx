import React, { useMemo } from 'react';
import { Heart } from 'lucide-react';
import PlaceCard from '../components/PlaceCard';

export default function FavoritesTab({
  favorites,
  placeType,
  onSelect,
  onToggleFav,
  onRemove,
}) {
  const filtered = useMemo(() => {
    if (!placeType) return favorites;
    return favorites.filter((p) => p.place_type === placeType);
  }, [favorites, placeType]);

  return (
    <>
      <h2 className="section-title">
        {placeType ? `Избранное: ${placeType}` : 'Сохранённые места'}{' '}
        <span className="count">{filtered.length}</span>
      </h2>

      {filtered.length === 0 ? (
        <div className="empty">
          <div className="empty-icon">
            <Heart size={36} />
          </div>
          <h3>
            {placeType && favorites.length > 0
              ? 'Нет совпадений'
              : 'Пока ничего не сохранено'}
          </h3>
          <p>
            {placeType && favorites.length > 0
              ? `Среди избранного нет мест типа «${placeType}»`
              : 'Нажимайте на ♥, чтобы сохранить'}
          </p>
        </div>
      ) : (
        filtered.map((place) => (
          <PlaceCard
            key={place.id}
            place={place}
            isFav
            onSelect={() => onSelect(place)}
            onToggleFav={() => onToggleFav(place)}
            onDelete={() => onRemove(place)}
          />
        ))
      )}
    </>
  );
}