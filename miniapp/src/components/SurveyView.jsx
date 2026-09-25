import React, { useState } from 'react';
import { Compass, Check, ArrowRight, ArrowLeft } from 'lucide-react';

const CITIES = ['Москва', 'Новосибирск', 'Санкт-Петербург'];
const CATEGORIES = ['Студенты', 'Пенсионеры', 'Участники СВО'];

export default function SurveyView({ onComplete, initialCity, initialCategory, isEdit = false }) {
  const [step, setStep] = useState(1);
  const [city, setCity] = useState(initialCity || 'Москва');
  const [category, setCategory] = useState(initialCategory || 'Студенты');

  return (
    <div className="survey-shell">
      <div className="survey-box">
        {!isEdit && (
          <>
            <div className="survey-logo"><Compass size={34} /></div>
            <h2 className="survey-title">Социальный Компас</h2>
            <p className="survey-subtitle">
              Найдём интересные места в вашем городе
            </p>
          </>
        )}
        {isEdit && (
          <h2 className="survey-title" style={{ marginBottom: 20 }}>Изменить данные</h2>
        )}

        {step === 1 ? (
          <>
            <div className="survey-question">Ваш город</div>
            <div className="options-grid">
              {CITIES.map((c) => (
                <div
                  key={c}
                  className={`option-btn ${city === c ? 'selected' : ''}`}
                  onClick={() => setCity(c)}
                >
                  <span>{c}</span>
                  {city === c && <Check size={18} />}
                </div>
              ))}
            </div>
            <div className="survey-actions">
              <button className="btn btn-primary btn-block" onClick={() => setStep(2)}>
                Далее <ArrowRight size={16} />
              </button>
            </div>
          </>
        ) : (
          <>
            <div className="survey-question">Ваша категория</div>
            <div className="options-grid">
              {CATEGORIES.map((c) => (
                <div
                  key={c}
                  className={`option-btn ${category === c ? 'selected' : ''}`}
                  onClick={() => setCategory(c)}
                >
                  <span>{c}</span>
                  {category === c && <Check size={18} />}
                </div>
              ))}
            </div>
            <div className="survey-actions">
              <button className="btn btn-ghost" onClick={() => setStep(1)}>
                <ArrowLeft size={16} /> Назад
              </button>
              <button className="btn btn-primary" onClick={() => onComplete(city, category)}>
                Готово <Check size={16} />
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}