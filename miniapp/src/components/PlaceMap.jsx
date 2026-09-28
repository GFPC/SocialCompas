import React, { useEffect, useRef } from 'react';
import L from 'leaflet';

// City default centers fallback
const CITY_CENTERS = {
  'Москва': [55.7558, 37.6173],
  'Санкт-Петербург': [59.9343, 30.3351],
  'Новосибирск': [55.0084, 82.9357],
};

function createCustomIcon(emoji = '📍') {
  return L.divIcon({
    className: 'custom-leaflet-marker',
    html: `<div style="
      background: #4F46E5;
      color: #fff;
      border-radius: 50%;
      width: 36px;
      height: 36px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 18px;
      box-shadow: 0 4px 10px rgba(79, 70, 229, 0.4);
      border: 2px solid white;
    ">${emoji}</div>`,
    iconSize: [36, 36],
    iconAnchor: [18, 36],
    popupAnchor: [0, -36],
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
  height = '320px',
  zoom = 12,
}) {
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);

  useEffect(() => {
    if (!mapContainerRef.current) return;

    // Cleanup previous map instance if initialized
    if (mapInstanceRef.current) {
      mapInstanceRef.current.remove();
      mapInstanceRef.current = null;
    }

    // Determine initial map center
    let center = CITY_CENTERS[city] || [55.7558, 37.6173];
    if (lat && lng) {
      center = [parseFloat(lat), parseFloat(lng)];
    } else if (places.length > 0 && places[0].lat && places[0].lng) {
      center = [parseFloat(places[0].lat), parseFloat(places[0].lng)];
    }

    // Initialize Leaflet map
    const map = L.map(mapContainerRef.current, {
      center,
      zoom,
      zoomControl: true,
    });

    // Free OpenStreetMap tile layer (No API Key required!)
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    }).addTo(map);

    mapInstanceRef.current = map;

    // Add markers
    const markers = [];

    if (places && places.length > 0) {
      places.forEach((p) => {
        if (!p.lat || !p.lng) return;
        const pLat = parseFloat(p.lat);
        const pLng = parseFloat(p.lng);
        const icon = createCustomIcon(p.place_type === 'Музей' ? '🏛️' : (p.place_type === 'Зоопарк' ? '🦁' : '📍'));

        const marker = L.marker([pLat, pLng], { icon }).addTo(map);

        const popupContent = document.createElement('div');
        popupContent.style.padding = '4px';
        popupContent.style.maxWidth = '220px';
        popupContent.innerHTML = `
          <strong style="font-size: 14px; color: #111827;">${p.title}</strong>
          ${p.place_type ? `<div style="font-size: 11px; color: #6B7280; margin-top: 2px;">${p.place_type}</div>` : ''}
          ${p.promo_text ? `<div style="font-size: 12px; color: #059669; font-weight: 600; margin-top: 4px;">🏷️ ${p.promo_text}</div>` : ''}
          ${p.address ? `<div style="font-size: 11px; color: #4B5563; margin-top: 4px;">📍 ${p.address}</div>` : ''}
        `;

        if (onSelectPlace) {
          const btn = document.createElement('button');
          btn.textContent = 'Подробнее';
          btn.style.marginTop = '8px';
          btn.style.width = '100%';
          btn.style.padding = '6px 12px';
          btn.style.background = '#4F46E5';
          btn.style.color = '#ffffff';
          btn.style.border = 'none';
          btn.style.borderRadius = '6px';
          btn.style.cursor = 'pointer';
          btn.style.fontSize = '12px';
          btn.style.fontWeight = '600';
          btn.onclick = () => onSelectPlace(p);
          popupContent.appendChild(btn);
        }

        marker.bindPopup(popupContent);
        markers.push(marker);
      });

      if (markers.length > 1) {
        const group = L.featureGroup(markers);
        map.fitBounds(group.getBounds().pad(0.2));
      }
    } else if (lat && lng) {
      const pLat = parseFloat(lat);
      const pLng = parseFloat(lng);
      const icon = createCustomIcon('📍');
      const marker = L.marker([pLat, pLng], { icon }).addTo(map);

      const popupHtml = `
        <strong style="font-size: 14px; color: #111827;">${title || 'Место'}</strong>
        ${address ? `<div style="font-size: 11px; color: #4B5563; margin-top: 4px;">📍 ${address}</div>` : ''}
      `;
      marker.bindPopup(popupHtml).openPopup();
    }

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, [lat, lng, address, title, places, city, zoom]);

  return (
    <div style={{ marginTop: 14, borderRadius: 16, overflow: 'hidden', border: '1px solid var(--border-color, #E5E7EB)' }}>
      <div ref={mapContainerRef} style={{ width: '100%', height }} />
    </div>
  );
}