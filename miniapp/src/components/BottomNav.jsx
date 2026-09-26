import React from 'react';
import { Home, Heart, MessageCircle, User } from 'lucide-react';

const TABS = [
  { id: 'places',    icon: Home,            label: 'Главная' },
  { id: 'favorites', icon: Heart,           label: 'Избранное' },
  { id: 'chat',      icon: MessageCircle,   label: 'Чат с ИИ' },
  { id: 'profile',   icon: User,            label: 'Профиль' },
];

export default function BottomNav({ active, onChange, favoritesCount = 0 }) {
  return (
    <nav className="bottom-nav">
      {TABS.map(({ id, icon: Icon, label }) => (
        <button
          key={id}
          className={`nav-item ${active === id ? 'active' : ''}`}
          onClick={() => onChange(id)}
        >
          <Icon size={22} strokeWidth={active === id ? 2.4 : 2} />
          <span>{label}</span>
          {id === 'favorites' && favoritesCount > 0 && (
            <span className="badge-count">{favoritesCount}</span>
          )}
        </button>
      ))}
    </nav>
  );
}