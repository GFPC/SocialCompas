import React, { useEffect, useMemo, useRef, useState } from 'react';

const CITY_CENTERS = {
  'Москва': [55.7558, 37.6173],
  'Санкт-Петербург': [59.9343, 30.3351],
  'Новосибирск': [55.0084, 82.9357],
};

const YMAPS_KEY = import.meta.env.VITE_YMAPS_KEY || '';
const GEO_CACHE_KEY = 'sc_geocache_v1';
const GEO_CONCURRENCY = 4;

const esc = (v) =>
  String(v ?? '').replace(/[&<>"']/g, (ch) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch]));

function loadYandexMapsScript() {
  return new Promise((resolve, reject) => {
    if (window.ymaps) {
      window.ymaps.ready(resolve);
      return;
    }

    const existingScript = document.getElementById('ymaps-script');
    if (existingScript) {
      existingScript.addEventListener('load', () => window.ymaps.ready(resolve));
      existingScript.addEventListener('error', reject);
      return;
    }

    const script = document.createElement('script');
    script.id = 'ymaps-script';
    script.src = `https://api-maps.yandex.ru/2.1/?lang=ru_RU${YMAPS_KEY ? `&apikey=${YMAPS_KEY}` : ''}`;
    script.type = 'text/javascript';
    script.async = true;
    script.onload = () => window.ymaps.ready(resolve);
    script.onerror = reject;
    document.head.appendChild(script);
  });
}

function readGeoCache() {
  try {
    return JSON.parse(localStorage.getItem(GEO_CACHE_KEY) || '{}');
  } catch {
    return {};
  }
}

function writeGeoCache(cache) {
  try {
    localStorage.setItem(GEO_CACHE_KEY, JSON.stringify(cache));
  } catch {}
}

async function geocodeAddress(city, address, cache) {
  const query = `${city}, ${address}`;
  if (cache[query]) return cache[query];
  try {
    const res = await window.ymaps.geocode(query, { results: 1 });
    const first = res.geoObjects.get(0);
    const coords = first ? first.geometry.getCoordinates() : null;
    if (coords) cache[query] = coords;
    return coords;
  } catch {
    return null;
  }
}

// У одного места может быть несколько адресов через «;» — у каждого своя метка.
function splitAddresses(address) {
  return String(address || '')
    .split(/[;\n]+/)
    .map((a) => a.trim())
    .filter(Boolean);
}

function readStoredPoints(place) {
  let pts = place.points;
  if (typeof pts === 'string') {
    try {
      pts = JSON.parse(pts);
    } catch {
      pts = [];
    }
  }
  return (Array.isArray(pts) ? pts : [])
    .filter((p) => p && p.lat && p.lng)
    .map((p) => ({ coords: [parseFloat(p.lat), parseFloat(p.lng)], address: p.address }));
}

async function resolvePlacePoints(place, fallbackCity, cache) {
  // 1. Координаты, посчитанные на сервере (scripts/geocode_places.py)
  const stored = readStoredPoints(place);
  if (stored.length > 0) return stored;
  if (place.lat && place.lng) {
    return [{ coords: [parseFloat(place.lat), parseFloat(place.lng)], address: place.address }];
  }
  const city = place.city || fallbackCity;
  const points = [];
  for (const address of splitAddresses(place.address)) {
    const coords = await geocodeAddress(city, address, cache);
    if (coords) points.push({ coords, address });
  }
  return points;
}

async function runLimited(items, worker, limit, isCancelled) {
  let next = 0;
  const runners = Array.from({ length: Math.min(limit, items.length) }, async () => {
    while (next < items.length && !isCancelled()) {
      const i = next++;
      await worker(items[i], i);
    }
  });
  await Promise.all(runners);
}

function presetFor(type) {
  if (type === 'Музей') return 'islands#violetIcon';
  if (type === 'Зоопарк') return 'islands#greenIcon';
  return 'islands#blueIcon';
}

// Константа, а не `places = []` в параметрах: литерал создаёт новый массив при каждом рендере,
// и эффект карты пересоздавал её (мерцание) при любом обновлении родителя.
const NO_PLACES = [];

export default function PlaceMap({
  lat,
  lng,
  address,
  title,
  places = NO_PLACES,
  points: detailPoints,
  city = 'Москва',
  onSelectPlace,
  height = '360px',
  zoom,
}) {
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const [mapLoaded, setMapLoaded] = useState(false);

  // Карта пересоздаётся только при реальном изменении данных, а не при смене идентичности массивов/объектов
  // (родитель перерисовывается каждые ~20 с из-за синхронизации избранного и профиля).
  const dataKey = useMemo(
    () =>
      JSON.stringify([
        places.map((p) => [p.id, p.address, p.lat, p.lng, p.points]),
        detailPoints ?? null,
      ]),
    [places, detailPoints]
  );

  useEffect(() => {
    let cancelled = false;
    const isCancelled = () => cancelled;

    const destroyMap = () => {
      if (mapInstanceRef.current) {
        try {
          mapInstanceRef.current.destroy();
        } catch {}
        mapInstanceRef.current = null;
      }
    };

    const fitToMarkers = (map, count) => {
      if (count === 0) return;
      if (count === 1) {
        map.setCenter(map.geoObjects.get(0).geometry.getCoordinates(), zoom || 15);
        return;
      }
      map
        .setBounds(map.geoObjects.getBounds(), { checkZoomRange: true, zoomMargin: 40 })
        .then(() => {
          if (map.getZoom() > 16) map.setZoom(16);
        })
        .catch(() => {});
    };

    const addMarker = (map, coords, properties, options, onClick) => {
      const placemark = new window.ymaps.Placemark(coords, properties, options);
      if (onClick) placemark.events.add('click', onClick);
      map.geoObjects.add(placemark);
    };

    const init = async () => {
      await loadYandexMapsScript();
      if (cancelled || !mapContainerRef.current) return;
      destroyMap();

      const cache = readGeoCache();
      const baseCenter = CITY_CENTERS[city] || CITY_CENTERS['Москва'];
      const map = new window.ymaps.Map(
        mapContainerRef.current,
        { center: baseCenter, zoom: zoom || 11, controls: ['zoomControl', 'fullscreenControl'] },
        { suppressMapOpenBlock: true }
      );
      mapInstanceRef.current = map;
      setMapLoaded(true);

      let markerCount = 0;

      if (places.length > 0) {
        await runLimited(
          places,
          async (p) => {
            const points = await resolvePlacePoints(p, city, cache);
            if (cancelled) return;
            points.forEach(({ coords, address: pointAddress }) => {
              const body = `
                <div style="font-size: 12px; color: #374151; margin-top: 4px;">
                  ${p.place_type ? `<div style="color: #4F46E5; font-weight: 600; font-size: 11px;">${esc(p.place_type)}</div>` : ''}
                  ${p.promo_text ? `<div style="color: #059669; font-weight: 600; margin-top: 4px;">🏷️ ${esc(p.promo_text)}</div>` : ''}
                  ${pointAddress ? `<div style="color: #6B7280; margin-top: 4px; font-size: 11px;">📍 ${esc(pointAddress)}</div>` : ''}
                </div>`;
              addMarker(
                map,
                coords,
                {
                  hintContent: esc(p.title),
                  balloonContentHeader: `<div style="font-weight: bold; font-size: 14px; color: #111827;">${esc(p.title)}</div>`,
                  balloonContentBody: body,
                },
                { preset: presetFor(p.place_type) },
                onSelectPlace ? () => onSelectPlace(p) : null
              );
              markerCount += 1;
            });
          },
          GEO_CONCURRENCY,
          isCancelled
        );
      } else if (lat || lng || address) {
        const points = await resolvePlacePoints({ lat, lng, address, city, points: detailPoints }, city, cache);
        if (cancelled) return;
        points.forEach(({ coords, address: pointAddress }) => {
          addMarker(
            map,
            coords,
            {
              hintContent: esc(title || 'Место'),
              balloonContentHeader: `<div style="font-weight: bold; font-size: 14px; color: #111827;">${esc(title || 'Место')}</div>`,
              balloonContentBody: pointAddress
                ? `<div style="font-size: 12px; color: #4B5563; margin-top: 4px;">📍 ${esc(pointAddress)}</div>`
                : '',
            },
            { preset: 'islands#redIcon' }
          );
          markerCount += 1;
        });
      }

      if (cancelled) return;
      writeGeoCache(cache);
      fitToMarkers(map, markerCount);
    };

    init().catch((err) => console.error('Yandex Maps error:', err));

    return () => {
      cancelled = true;
      destroyMap();
      setMapLoaded(false);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lat, lng, address, title, dataKey, city, zoom]);

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
