import React, { useEffect, useRef, useState } from 'react';

const CITY_CENTERS = {
  'Москва': [55.7558, 37.6173],
  'Санкт-Петербург': [59.9343, 30.3351],
  'Новосибирск': [55.0084, 82.9357],
};

function loadYandexMapsScript() {
  return new Promise((resolve, reject) => {
    if (window.ymaps) {
      window.ymaps.ready(resolve);
      return;
    }

    const existingScript = document.getElementById('ymaps-script');
    if (existingScript) {
      existingScript.addEventListener('load', () => {
        window.ymaps.ready(resolve);
      });
      existingScript.addEventListener('error', reject);
      return;
    }

    const script = document.createElement('script');
    script.id = 'ymaps-script';
    script.src = 'https://api-maps.yandex.ru/2.1/?lang=ru_RU';
    script.type = 'text/javascript';
    script.async = true;
    script.onload = () => {
      window.ymaps.ready(resolve);
    };
    script.onerror = reject;
    document.head.appendChild(script);
  });
}

function getPlaceCoords(p, city, index = 0) {
  if (p.lat && p.lng) {
    return [parseFloat(p.lat), parseFloat(p.lng)];
  }
  const targetCity = p.city || city;
  const base = CITY_CENTERS[targetCity] || CITY_CENTERS[city] || CITY_CENTERS['Москва'];
  const seed = (p.id || (index + 1)) * 37 + (p.title ? p.title.length : 7) * 19;
  const latOffset = (((seed * 11) % 120) - 60) * 0.0012;
  const lngOffset = (((seed * 23) % 120) - 60) * 0.0022;
  return [base[0] + latOffset, base[1] + lngOffset];
}

export default function PlaceMap({
  lat,
  lng,
  address,
  title,
  places = [],
  city = 'Москва',
  onSelectPlace,
  height = '360px',
  zoom,
}) {
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const [mapLoaded, setMapLoaded] = useState(false);

  // Определяем подходящий масштаб: 15 для конкретного места, 13 для списка по городу
  const targetZoom = zoom || (lat && lng ? 15 : 13);

  useEffect(() => {
    let isMounted = true;

    loadYandexMapsScript()
      .then(() => {
        if (!isMounted || !mapContainerRef.current) return;
        initMap();
        setMapLoaded(true);
      })
      .catch((err) => {
        console.error('Yandex Maps API load error:', err);
      });

    return () => {
      isMounted = false;
      if (mapInstanceRef.current) {
        try {
          mapInstanceRef.current.destroy();
        } catch {
        }
        mapInstanceRef.current = null;
      }
    };
  }, [lat, lng, address, title, places, city, zoom]);

  const initMap = () => {
    if (!window.ymaps || !mapContainerRef.current) return;

    if (mapInstanceRef.current) {
      try {
        mapInstanceRef.current.destroy();
      } catch {
      }
      mapInstanceRef.current = null;
    }

    let center = CITY_CENTERS[city] || [55.7558, 37.6173];
    if (lat && lng) {
      center = [parseFloat(lat), parseFloat(lng)];
    } else if (places.length > 0) {
      center = getPlaceCoords(places[0], city, 0);
    }

    const map = new window.ymaps.Map(
      mapContainerRef.current,
      {
        center,
        zoom: targetZoom,
        controls: ['zoomControl', 'fullscreenControl'],
      },
      {
        suppressMapOpenBlock: true,
      }
    );

    mapInstanceRef.current = map;

    const geoObjects = [];

    if (places && places.length > 0) {
      places.forEach((p, idx) => {
        const [pLat, pLng] = getPlaceCoords(p, city, idx);

        const balloonContentHeader = `<div style="font-weight: bold; font-size: 14px; color: #111827;">${p.title}</div>`;
        const balloonContentBody = `
          <div style="font-size: 12px; color: #374151; margin-top: 4px;">
            ${p.place_type ? `<div style="color: #4F46E5; font-weight: 600; font-size: 11px;">${p.place_type}</div>` : ''}
            ${p.promo_text ? `<div style="color: #059669; font-weight: 600; margin-top: 4px;">🏷️ ${p.promo_text}</div>` : ''}
            ${p.address ? `<div style="color: #6B7280; margin-top: 4px; font-size: 11px;">📍 ${p.address}</div>` : ''}
          </div>
        `;

        const placemark = new window.ymaps.Placemark(
          [pLat, pLng],
          {
            hintContent: p.title,
            balloonContentHeader,
            balloonContentBody,
          },
          {
            preset: p.place_type === 'Музей' ? 'islands#violetIcon' : (p.place_type === 'Зоопарк' ? 'islands#greenIcon' : 'islands#blueIcon'),
          }
        );

        if (onSelectPlace) {
          placemark.events.add('click', () => {
            onSelectPlace(p);
          });
        }

        map.geoObjects.add(placemark);
        geoObjects.push(placemark);
      });

      if (geoObjects.length > 0) {
        // Устанавливаем границы меток, но ограничиваем zoom от отдаления на весь мир (минимум 12, максимум 15)
        map.setBounds(map.geoObjects.getBounds(), { checkZoomRange: true, zoomMargin: 40 })
          .then(() => {
            if (map.getZoom() < 12) {
              map.setZoom(12);
            } else if (map.getZoom() > 15) {
              map.setZoom(15);
            }
          })
          .catch(() => {
            map.setCenter(center, targetZoom);
          });
      }
    } else if (lat || lng || address) {
      const pLat = lat ? parseFloat(lat) : center[0];
      const pLng = lng ? parseFloat(lng) : center[1];

      const placemark = new window.ymaps.Placemark(
        [pLat, pLng],
        {
          hintContent: title || 'Место',
          balloonContentHeader: `<div style="font-weight: bold; font-size: 14px; color: #111827;">${title || 'Место'}</div>`,
          balloonContentBody: address ? `<div style="font-size: 12px; color: #4B5563; margin-top: 4px;">📍 ${address}</div>` : '',
        },
        {
          preset: 'islands#redIcon',
        }
      );

      map.geoObjects.add(placemark);
      map.setCenter([pLat, pLng], 15);
    }
  };

  return (
    <div style={{ marginTop: 14, borderRadius: 16, overflow: 'hidden', border: '1px solid var(--border-color, #E5E7EB)', position: 'relative' }}>
      {!mapLoaded && (
        <div style={{
          height,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: '#F9FAFB',
          color: '#6B7280',
          fontSize: 13,
        }}>
          Загрузка Яндекс Карт...
        </div>
      )}
      <div
        ref={mapContainerRef}
        style={{ width: '100%', height, display: mapLoaded ? 'block' : 'none' }}
      />
    </div>
  );
}