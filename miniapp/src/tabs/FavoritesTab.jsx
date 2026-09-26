import React, { useMemo } from 'react';
import { Heart } from 'lucide-react';
import PlaceCard from '../components/PlaceCard';

export default function FavoritesTab({
  favorites,
  selectedTypes,
  onSelect,
  onToggleFav,
  onRemove,
}) {
  const filtered = useMemo(() => {
    if (!selectedTypes || selectedTypes.length === 0) return favorites;
    return favorites.filter((p) => selectedTypes.includes(p.place_type));
  }, [favorites, selectedTypes]);

  const headerLabel =
    selectedTypes && selectedTypes.length > 0
      ? `Избранное: ${selectedTypes.join(', ')}`
      : 'Сохранённые места';

  return (
    <>
      <h2 className="section-title">
        {headerLabel} <span className="count">{filtered.length}</span>
      </h2>

      {filtered.length === 0 ? (
        <div className="empty">
          <div className="empty-icon"><Heart size={36} /></div>
          <h3>
            {selectedTypes?.length && favorites.length > 0
              ? 'Нет совпадений'
              : 'Пока ничего не сохранено'}
          </h3>
          <p>
            {selectedTypes?.length && favorites.length > 0
              ? `Среди избранного нет мест выбранных типов`
              : 'Нажимайте ♥ на карточках мест, чтобы добавить сюда'}
          </p>
        </div>
      ) : (
  <div className="favorites-grid">
    {filtered.map((place) => (
      <PlaceCard
        key={place.id}
        place={place}
        isFav
        onSelect={() => onSelect(place)}
        onToggleFav={() => onToggleFav(place)}
        onDelete={() => onRemove(place)}
      />
    ))}
  </div>
)}
    </>
  );
}