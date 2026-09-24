import React from 'react';
import { User, MapPin, Award, Pencil } from 'lucide-react';

export default function ProfileTab({ city, category, onEdit }) {
  return (
    <>
      <div className="profile-hero">
        <div className="avatar"><User size={30} /></div>
        <h2>Это Вы</h2>
        <p>Персональные рекомендации по вашим настройкам</p>
      </div>

      <div className="profile-card">
        <div className="info-row">
          <div className="icon-wrap"><MapPin size={18} /></div>
          <div>
            <span className="label">Ваш город</span>
            <span className="value">{city}</span>
          </div>
        </div>
        <div className="info-row">
          <div className="icon-wrap"><Award size={18} /></div>
          <div>
            <span className="label">Ваша категория</span>
            <span className="value">{category}</span>
          </div>
        </div>
      </div>

      <button
        className="btn btn-primary btn-block"
        onClick={onEdit}
      >
        <Pencil size={16} /> Изменить
      </button>
    </>
  );
}