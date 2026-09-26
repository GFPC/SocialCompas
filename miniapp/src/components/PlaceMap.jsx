import React from 'react';

export default function PlaceMap({ address, height = '250px' }) {
  if (!address) return null;

  const embedUrl = `https://www.google.com/maps?q=${encodeURIComponent(address)}&hl=ru&output=embed`;

  return (
    <div style={{ marginTop: 14, borderRadius: 12, overflow: 'hidden' }}>
      <iframe
        title={`Карта: ${address}`}
        src={embedUrl}
        width="100%"
        height={height}
        style={{ border: 0, display: 'block' }}
        allowFullScreen
        loading="lazy"
        referrerPolicy="no-referrer-when-downgrade"
      />
    </div>
  );
}