import React from 'react';
import { X, Check, SlidersHorizontal } from 'lucide-react';

export default function FilterSheet({ types, selected, onSelect, onClose }) {
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-sheet" onClick={(e) => e.stopPropagation()}>
        <div className="modal-handle" />

        <div style={{ display: 'flex', alignItems: 'center', marginBottom: 16 }}>
          <div
            style={{
              width: 36, height: 36, borderRadius: 10,
              background: 'var(--primary-soft)',
              color: 'var(--primary)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              marginRight: 10,
            }}
          >
            <SlidersHorizontal size={18} />
          </div>
          <h3 className="modal-title" style={{ marginBottom: 0, flex: 1 }}>
            Тип места
          </h3>
          <button className="icon-btn" onClick={onClose}>
            <X size={18} />
          </button>
        </div>

        <button
          className={`option-btn ${!selected ? 'selected' : ''}`}
          style={{ marginBottom: 8 }}
          onClick={() => onSelect(null)}
        >
          <span>Все типы</span>
          {!selected && <Check size={18} />}
        </button>

        {types.length === 0 && (
          <p
            style={{
              textAlign: 'center',
              color: 'var(--text-muted)',
              padding: 20,
              fontSize: 13,
            }}
          >
            Пока нет доступных типов — сначала загрузите места
          </p>
        )}

        {types.map((t) => (
          <button
            key={t}
            className={`option-btn ${selected === t ? 'selected' : ''}`}
            style={{ marginBottom: 8 }}
            onClick={() => onSelect(t)}
          >
            <span>{t}</span>
            {selected === t && <Check size={18} />}
          </button>
        ))}
      </div>
    </div>
  );
}