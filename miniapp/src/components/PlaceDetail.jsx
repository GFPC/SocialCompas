import React from 'react';
import {
  ArrowLeft, Heart, MapPin, Clock,
  ExternalLink, Share2, Globe,
} from 'lucide-react';
import { getPlaceImage } from '../utils/placeImages';
import PlaceMap from './PlaceMap';

const CATEGORY_EMOJI = {
  // Категории пользователей
  'Студенты': '🎓',
  'Пенсионеры': '👵',
  'Участники СВО': '🎖',

  // Типы мест
  'Аквапарк': '🏊',
  'Музей': '🏛️',
  'Бильярдный клуб': '🎱',
  'Боулинг клуб': '🎳',
  'Боулинг центр': '🎳',
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

function isMapUrl(url) {
  if (!url) return false;
  const u = url.toLowerCase();
  return (
    u.includes('maps') ||
    u.includes('yandex.ru/maps') ||
    u.includes('google.com/maps') ||
    u.includes('2gis')
  );
}

export default function PlaceDetail({
  place, isFav, onToggleFav, onBack, showToast,
}) {
  const image = getPlaceImage(place);
  const emoji = getEmoji(place);

  const handleShare = async () => {
    const text = `${place.title}\n${place.promo_text || ''}\n${place.address || ''}`;

    // 1. Всегда копируем в буфер и показываем тост
    try {
      await navigator.clipboard.writeText(text);
      showToast?.('Скопировано в буфер');
    } catch {
      showToast?.('Не удалось скопировать');
    }

    // 2. Если браузер умеет нативный share — предлагаем и его
    if (navigator.share) {
      try {
        await navigator.share({ title: place.title, text });
      } catch (e) {
        // пользователь отменил — не проблема, ссылка уже в буфере
      }
    }
  };

  const linkIsMap = isMapUrl(place.map_url);
  const linkLabel = linkIsMap ? 'Открыть на карте' : 'Перейти на сайт';
  const LinkIcon = linkIsMap ? MapPin : Globe;

  return (
    <div>
      <button className="detail-back" onClick={onBack}>
        <ArrowLeft size={16} /> Назад
      </button>

      <div className="detail-hero">
        <div className="place-banner">
          {image ? (
            <img src={image} alt={place.title} />
          ) : (
            <span className="banner-emoji" style={{ fontSize: 72 }}>
              {emoji}
            </span>
          )}
          {place.place_type && <span className="banner-tag">{place.place_type}</span>}
        </div>
        <div className="hero-body">
          <h1>{place.title}</h1>
          {place.promo_text && <p className="hero-desc">{place.promo_text}</p>}
        </div>
      </div>

      {place.promo_text && (
        <div className="promo-banner">
          <div className="promo-label">Акция</div>
          <div className="promo-text">{place.promo_text}</div>
        </div>
      )}

      <div className="profile-card" style={{ padding: '4px 16px' }}>
        {place.schedule && (
          <div className="info-row">
            <div className="icon-wrap">
              <Clock size={18} />
            </div>
            <div>
              <span className="label">Время работы</span>
              <span className="value">{place.schedule}</span>
            </div>
          </div>
        )}

        {place.address && (
          <div className="info-row">
            <div className="icon-wrap">
              <MapPin size={18} />
            </div>
            <div>
              <span className="label">Как добраться?</span>
              <span className="value">{place.address}</span>
            </div>
          </div>
        )}
      </div>

      {/* Встроенная карта по адресу */}
      {place.address && <PlaceMap address={place.address} />}

      {/* Ссылка из БД — на сайт или на карту */}
      {place.map_url && (
        <a
          className="map-link"
          href={place.map_url}
          target="_blank"
          rel="noreferrer"
        >
          <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <LinkIcon size={18} /> {linkLabel}
          </span>
          <ExternalLink size={16} />
        </a>
      )}

      <div className="detail-actions">
        <button
          className={`btn ${isFav ? 'btn-ghost' : 'btn-primary'}`}
          onClick={onToggleFav}
        >
          <Heart size={18} fill={isFav ? 'currentColor' : 'none'} />
          {isFav ? 'В избранном' : 'В избранное'}
        </button>

        <button className="btn btn-outline" onClick={handleShare}>
          <Share2 size={18} /> Поделиться
        </button>
      </div>

      <p
        style={{
          fontSize: 12,
          color: 'var(--text-soft)',
          fontStyle: 'italic',
          marginTop: 16,
          textAlign: 'center',
          lineHeight: 1.5,
        }}
      >
        *Скидки и льготы предоставляются при предъявлении документа.
        <br />
        Информация носит справочный характер и не является публичной офертой (ст. 437 ГК РФ).
        <br />
        Уточняйте условия у представителей акций.
      </p>
    </div>
  );
}