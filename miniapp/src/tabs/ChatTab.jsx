import React, { useState, useRef, useEffect } from 'react';
import { Send, Sparkles, Bot, User } from 'lucide-react';
import { sendChatMessage } from '../api';

const SUGGESTIONS = [
  'Куда сходить со студенческим?',
  'Есть ли скидки в музеи?',
  'Где в городе аквапарк?',
  'Что бесплатно для льготников?',
];

export default function ChatTab({ city = 'Москва', category = 'Студенты' }) {
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      role: 'ai',
      text: `Привет! Я ИИ-ассистент SocialCompass. Подскажу акции и места в г. ${city} для категории «${category}». О чём хотите узнать?`,
    },
  ]);
  const [input, setInput] = useState('');
  const [typing, setTyping] = useState(false);

  const bottomRef = useRef(null);

  // Скролл вниз при новых сообщениях
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, typing]);

  const handleSend = async (text) => {
    const userText = text.trim();
    if (!userText || typing) return;

    const userMsg = {
      id: 'u_' + Date.now(),
      role: 'user',
      text: userText,
    };

    const newMessages = [...messages, userMsg];
    setMessages(newMessages);
    setInput('');
    setTyping(true);

    try {
      const aiReplyText = await sendChatMessage(newMessages, city, category);
      const aiMsg = {
        id: 'a_' + Date.now(),
        role: 'ai',
        text: aiReplyText,
      };
      setMessages((prev) => [...prev, aiMsg]);
    } catch (err) {
      console.error('[ChatTab] Error:', err);
      const errorMsg = {
        id: 'err_' + Date.now(),
        role: 'ai',
        text: err.message || 'Произошла ошибка при обращении к ИИ. Попробуйте ещё раз позже.',
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setTyping(false);
    }
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