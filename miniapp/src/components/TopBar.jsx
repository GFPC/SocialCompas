import React from 'react';
import { SlidersHorizontal, X } from 'lucide-react';

function filterLabel(selectedTypes) {
  if (!selectedTypes || selectedTypes.length === 0) return 'Все типы';
  if (selectedTypes.length === 1) return selectedTypes[0];
  return `${selectedTypes.length} типа`;
}

export default function TopBar({ city, selectedTypes, onFilterClick, onClearFilter }) {
  const hasFilter = selectedTypes && selectedTypes.length > 0;
  const label = filterLabel(selectedTypes);

  return (
    <div className="top-bar">
      {/* Город — просто отображение */}
      <div className="pill pill-static">
        <div style={{ textAlign: 'left', minWidth: 0 }}>
          <span className="pill-label">Ваш город</span>
          <span className="pill-value">{city}</span>
        </div>
      </div>

      {/* Фильтр по типам мест */}
      {hasFilter ? (
        <button className="pill filter active-filter" onClick={onFilterClick}>
          <div style={{ textAlign: 'left', minWidth: 0 }}>
            <span className="pill-label">Фильтр</span>
            <span className="pill-value" style={{ fontSize: 12 }}>{label}</span>
          </div>
          <span
            role="button"
            onClick={(e) => { e.stopPropagation(); onClearFilter(); }}
            style={{
              display: 'flex', alignItems: 'center',
              color: 'var(--primary)', padding: 2,
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