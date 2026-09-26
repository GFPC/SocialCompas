import React from 'react';
import { X, Check, SlidersHorizontal, RotateCcw } from 'lucide-react';

export default function FilterSheet({
  types,
  selected,       // массив выбранных типов
  onToggle,       // (type) => void
  onClear,        // () => void
  onClose,
}) {
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

                  {selected.length > 0 && (
                    <div
                      style={{
                        fontSize: 12,
                        color: 'var(--text-muted)',
                        marginBottom: 10,
                      }}
                    >
                      Выбрано: {selected.length}
                    </div>
                  )}

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

                  {types.map((t) => {
                    const isSelected = selected.includes(t);
                    return (
                      <button
            key={t}
            className={`option-btn ${isSelected ? 'selected' : ''}`}
            style={{ marginBottom: 8 }}
            onClick={() => onToggle(t)}
          >
            <span style={{ flex: 1, paddingRight: 12 }}>{t}</span>
            <span
              style={{
                width: 22,
                height: 22,
                minWidth: 22,
                borderRadius: 6,
                border: isSelected
                  ? '2px solid var(--primary)'
                  : '1.5px solid var(--border)',
                background: isSelected ? 'var(--primary)' : 'transparent',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#fff',
                flexShrink: 0,
              }}
            >
              {isSelected && <Check size={14} strokeWidth={3} />}
            </span>
          </button>
          );
        })}

        <div style={{ display: 'flex', gap: 8, marginTop: 16 }}>
          <button
            className="btn btn-ghost"
            onClick={onClear}
            disabled={selected.length === 0}
            style={{
              flex: 1,
              opacity: selected.length === 0 ? 0.5 : 1,
            }}
          >
            <RotateCcw size={16} /> Сбросить
          </button>
          <button className="btn btn-primary" onClick={onClose} style={{ flex: 1 }}>
            Готово
          </button>
        </div>
      </div>
    </div>
  );
}