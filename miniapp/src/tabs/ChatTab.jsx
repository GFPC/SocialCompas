import React, { useState, useRef, useEffect } from 'react';
import { Send, Sparkles, Bot, User } from 'lucide-react';

const SUGGESTIONS = [
  'Куда сходить со студенческим?',
  'Есть ли скидки в музеи?',
  'Где поиграть в бильярд?',
  'Что бесплатно для студентов?',
];

// === Заглушка ИИ. Когда будет реальный API — заменим на fetch ===
function mockAIResponse(userText) {
  const t = userText.toLowerCase();
  if (t.includes('бильярд')) {
    return 'По бильярду советую «Фабрика на ткацкой» — скидка 40% на игру. Адрес: ул. Ткацкая, д. 5, стр. 7. Работают Пн–чт с 12:00 до 18:00.';
  }
  if (t.includes('музей') || t.includes('музеи')) {
    return 'В Москве для студентов есть скидки в Музей Маяковского (200 ₽) и Третьяковскую галерею (400 ₽). Оба работают в будни и выходные.';
  }
  if (t.includes('бесплат') || t.includes('бесплатн')) {
    return 'Бесплатный вход для студентов с московской регистрацией — в Московский зоопарк. Остальным — каждую третью среду месяца.';
  }
  if (t.includes('боулинг')) {
    return 'Боулинг со скидкой 50% — клуб «Самокат» на ул. Самокатной, д. 2к1. По будням с 12:00 до 18:00.';
  }
  if (t.includes('аквапарк')) {
    return 'Советую два аквапарка: «Мореон» (2350 ₽ по будням) и «Фэнтази» (скидка 30% в будни). Оба подходят для студентов.';
  }
  return 'Пока я только учусь, но могу подсказать места со скидками для студентов в Москве. Спросите про бильярд, музеи, аквапарки или боулинг — расскажу, где выгоднее.';
}

export default function ChatTab() {
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      role: 'ai',
      text: 'Привет! Я помогу найти скидки и интересные места для студентов. Что вас интересует?',
    },
  ]);
  const [input, setInput] = useState('');
  const [typing, setTyping] = useState(false);

  const bottomRef = useRef(null);

  // Скролл вниз при новых сообщениях
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, typing]);

  const handleSend = (text) => {
    const userText = text.trim();
    if (!userText) return;

    const userMsg = {
      id: 'u_' + Date.now(),
      role: 'user',
      text: userText,
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setTyping(true);

    // Имитация задержки ответа ИИ
    setTimeout(() => {
      const aiMsg = {
        id: 'a_' + Date.now(),
        role: 'ai',
        text: mockAIResponse(userText),
      };
      setMessages((prev) => [...prev, aiMsg]);
      setTyping(false);
    }, 900);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend(input);
    }
  };

  const showSuggestions = messages.length === 1;

  return (
    <div className="chat-wrap">
      <div className="chat-messages">
        {messages.map((m) => (
          <div
            key={m.id}
            className={`chat-row ${m.role === 'user' ? 'chat-row-user' : 'chat-row-ai'}`}
          >
            {m.role === 'ai' && (
              <div className="chat-avatar chat-avatar-ai">
                <Bot size={18} />
              </div>
            )}
            <div className={`chat-bubble chat-bubble-${m.role}`}>
              {m.text}
            </div>
            {m.role === 'user' && (
              <div className="chat-avatar chat-avatar-user">
                <User size={18} />
              </div>
            )}
          </div>
        ))}

        {typing && (
          <div className="chat-row chat-row-ai">
            <div className="chat-avatar chat-avatar-ai">
              <Bot size={18} />
            </div>
            <div className="chat-bubble chat-bubble-ai chat-typing">
              <span></span><span></span><span></span>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {showSuggestions && (
        <div className="chat-suggestions">
          <div className="chat-suggestions-label">
            <Sparkles size={13} /> Попробуйте спросить
          </div>
          <div className="chat-chips">
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                className="chat-chip"
                onClick={() => handleSend(s)}
              >
                {s}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="chat-input-row">
        <textarea
          className="chat-input"
          placeholder="Спросите что-нибудь..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          rows={1}
        />
        <button
          className="chat-send"
          onClick={() => handleSend(input)}
          disabled={!input.trim()}
        >
          <Send size={18} />
        </button>
      </div>
    </div>
  );
}