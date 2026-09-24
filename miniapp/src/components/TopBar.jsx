import React from 'react';
import { SlidersHorizontal, X } from 'lucide-react';

export default function TopBar({ city, placeType, onFilterClick, onClearFilter }) {
  return (
    <div className="top-bar">
      <div className="pill pill-static">
        <div style={{ textAlign: 'left', minWidth: 0 }}>
          <span className="pill-label">Ваш город</span>
          <span className="pill-value">{city}</span>
        </div>
      </div>

      {/* Фильтр */}
      {placeType ? (
        <button className="pill filter active-filter" onClick={onFilterClick}>
          <div style={{ textAlign: 'left', minWidth: 0 }}>
            <span className="pill-label">Фильтр</span>
            <span className="pill-value" style={{ fontSize: 12 }}>{placeType}</span>
          </div>
          <span
            role="button"
            onClick={(e) => { e.stopPropagation(); onClearFilter(); }}
            style={{
              display: 'flex', alignItems: 'center',
              color: 'var(--text-soft)', padding: 2,
            }}
          >
            <X size={14} />
          </span>
        </button>
      ) : (
        <button className="pill filter" onClick={onFilterClick}>
          <div style={{ textAlign: 'left', minWidth: 0 }}>
            <span className="pill-label">Фильтр</span>
            <span className="pill-value" style={{ fontSize: 12, color: 'var(--text-muted)' }}>
              Все типы
            </span>
          </div>
          <SlidersHorizontal size={14} style={{ color: 'var(--primary)', flexShrink: 0 }} />
        </button>
      )}
    </div>
  );
}