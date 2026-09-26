import React from 'react';
import { Heart, MapPin, Trash2 } from 'lucide-react';
import { getPlaceImage } from '../utils/placeImages';

const CATEGORY_EMOJI = {
  // Категории пользователей (fallback)
  'Студенты': '🎓',
  'Пенсионеры': '👵',
  'Участники СВО': '🎖',

  // Типы мест
  'Аквапарк': '🏊',
  'Музей': '🏛️',
  'Бильярдный клуб': '🎱',
  'Боулинг клуб': '🎳',
  'Зоопарк': '🦁',
  'Кинотеатр': '🎬',
  'Термальный комплекс': '♨️',
  'Котокафе': '🐱',
  'Кафе': '☕',
  'Спорт': '🏋️',

  default: '📍',
};

function getEmoji(place) {
  return (
    CATEGORY_EMOJI[place.place_type] ||
    CATEGORY_EMOJI[place.category] ||
    CATEGORY_EMOJI.default
  );
}

export default function PlaceCard({
  place,
  isFav,
  onSelect,
  onToggleFav,
  onDelete, // для избранного
}) {
  const image = getPlaceImage(place);
  const emoji = getEmoji(place);

  return (
    <article className="place-card clickable">
      <div className="place-banner" onClick={onSelect}>
        {image ? (
          <img src={image} alt={place.title} loading="lazy" />
        ) : (
          <span className="banner-emoji">{emoji}</span>
        )}
        {place.place_type && <span className="banner-tag">{place.place_type}</span>}
      </div>

      <div className="place-body" onClick={onSelect}>
        <h3 className="place-title">{place.title}</h3>
        {place.promo_text && (
          <p className="place-promo-line">{place.promo_text}</p>
        )}
        {place.address && (
          <p className="place-address">
            <MapPin size={13} /> {place.address}
          </p>
        )}
      </div>

      <div className="place-footer">
        <button
          className="btn btn-ghost btn-sm"
          onClick={(e) => { e.stopPropagation(); onSelect(); }}
        >
          Подробнее
        </button>

        <div className="actions">
          {onDelete && (
            <button
              className="icon-btn danger"
              onClick={(e) => { e.stopPropagation(); onDelete(); }}
              title="Удалить"
            >
              <Trash2 size={18} />
            </button>
          )}
          <button
            className={`icon-btn ${isFav ? 'active' : ''}`}
            onClick={(e) => { e.stopPropagation(); onToggleFav(); }}
            title={isFav ? 'Убрать из избранного' : 'В избранное'}
          >
            <Heart size={20} fill={isFav ? 'currentColor' : 'none'} />
          </button>
        </div>
      </div>
    </article>
  );
}