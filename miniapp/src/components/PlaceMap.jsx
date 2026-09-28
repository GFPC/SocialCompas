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

export default function PlaceMap({
  lat,
  lng,
  address,
  title,
  places = [],
  city = 'Москва',
  onSelectPlace,
  height = '340px',
  zoom = 12,
}) {
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const [mapLoaded, setMapLoaded] = useState(false);

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
      center = [parseFloat(lat), parseFloat(parseFloat(lng))];
    } else if (places.length > 0 && places[0].lat && places[0].lng) {
      center = [parseFloat(places[0].lat), parseFloat(places[0].lng)];
    }

    const map = new window.ymaps.Map(
      mapContainerRef.current,
      {
        center,
        zoom,
        controls: ['zoomControl', 'fullscreenControl'],
      },
      {
        suppressMapOpenBlock: true,
      }
    );

    mapInstanceRef.current = map;

    const geoObjects = [];

    if (places && places.length > 0) {
      places.forEach((p) => {
        if (!p.lat || !p.lng) return;
        const pLat = parseFloat(p.lat);
        const pLng = parseFloat(p.lng);

        const balloonContent = `
          <div style="padding: 6px; font-family: sans-serif; max-width: 220px;">
            <strong style="font-size: 14px; color: #111827;">${p.title}</strong>
            ${p.place_type ? `<div style="font-size: 11px; color: #4F46E5; font-weight: 600; margin-top: 2px;">${p.place_type}</div>` : ''}
            ${p.promo_text ? `<div style="font-size: 12px; color: #059669; font-weight: 600; margin-top: 4px;">🏷️ ${p.promo_text}</div>` : ''}
            ${p.address ? `<div style="font-size: 11px; color: #4B5563; margin-top: 4px;">📍 ${p.address}</div>` : ''}
          </div>
        `;

        const placemark = new window.ymaps.Placemark(
          [pLat, pLng],
          {
            hintContent: p.title,
            balloonContent,
          },
          {
            preset: 'islands#blueIcon',
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

      if (geoObjects.length > 1) {
        map.setBounds(map.geoObjects.getBounds(), { checkZoomRange: true, zoomMargin: 35 });
      }
    } else if (lat && lng) {
      const pLat = parseFloat(lat);
      const pLng = parseFloat(lng);

      const placemark = new window.ymaps.Placemark(
        [pLat, pLng],
        {
          hintContent: title || 'Место',
          balloonContent: `
            <div style="padding: 6px; font-family: sans-serif;">
              <strong style="font-size: 14px; color: #111827;">${title || 'Место'}</strong>
              ${address ? `<div style="font-size: 12px; color: #4B5563; margin-top: 4px;">📍 ${address}</div>` : ''}
            </div>
          `,
        },
        {
          preset: 'islands#redIcon',
        }
      );

      map.geoObjects.add(placemark);
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