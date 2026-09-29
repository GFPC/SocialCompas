// Тонкая обёртка над MAX Bridge (window.WebApp). Все вызовы безопасны вне MAX:
// если моста нет (обычный браузер), функции просто ничего не делают.
// Документация: https://dev.max.ru/docs/webapps/bridge

const bridge = () => (typeof window !== 'undefined' ? window.WebApp : undefined);

export const isInsideMax = () => Boolean(bridge()?.initData);

export const getInitData = () => bridge()?.initData || '';

/** Сообщаем MAX, что приложение готово (убирает нативный индикатор загрузки). */
export function notifyReady() {
  try {
    bridge()?.ready?.();
  } catch {}
}

/** Нативный вибро-отклик: 'success' | 'warning' | 'error'. */
export function haptic(type = 'success') {
  try {
    bridge()?.HapticFeedback?.notificationOccurred?.(type);
  } catch {}
}

/** Лёгкий отклик при выборе/переключении. */
export function hapticSelect() {
  try {
    bridge()?.HapticFeedback?.selectionChanged?.();
  } catch {}
}

/**
 * Нативная кнопка «Назад» в шапке MAX. Показывает её, пока задан handler,
 * и прячет, когда handler === null. Возвращает функцию очистки.
 */
export function bindBackButton(handler) {
  const back = bridge()?.BackButton;
  if (!back) return () => {};
  try {
    if (handler) {
      back.onClick?.(handler);
      back.show?.();
    } else {
      back.hide?.();
    }
  } catch {}
  return () => {
    try {
      if (handler) back.offClick?.(handler);
    } catch {}
  };
}

// Публичное имя бота (менять нельзя): нужно для ссылок вида https://max.ru/<bot>?startapp=<данные>
export const BOT_USERNAME = import.meta.env.VITE_MAX_BOT_USERNAME || 't294_hakaton_max_bot';

/** Ссылка, открывающая мини-приложение сразу на карточке места (получатель увидит её через start_param). */
export const placeDeepLink = (placeId) => `https://max.ru/${BOT_USERNAME}?startapp=place_${placeId}`;

/** Разбирает start_param запуска: 'place_123' → 123, иначе null. */
export function getStartPlaceId() {
  const raw = bridge()?.initDataUnsafe?.start_param;
  const m = /^place_(\d+)$/.exec(String(raw || ''));
  return m ? Number(m[1]) : null;
}

/**
 * Нативный экран «Поделиться» MAX (выбор чата/контакта). Документация:
 *  - shareMaxContent({text, link}) — все платформы, открывает интерфейс отправки внутри MAX;
 *  - shareContent({text, link}) — системный диалог, только iOS/Android.
 * Оба возвращают Promise и работают только сразу после клика пользователя — поэтому вызывать
 * нужно синхронно из обработчика клика. Возвращает { ok, method } либо { ok: false, reason }.
 */
export async function shareViaMax({ text, link }) {
  const b = bridge();
  if (!b) return { ok: false, reason: 'no-bridge' };

  const attempts = [];
  if (b.shareMaxContent) {
    attempts.push(['shareMaxContent', { text, link }]);
    // запасной формат: всё одним текстом (на случай, если клиент не принимает пару text+link)
    attempts.push(['shareMaxContent', { text: [text, link].filter(Boolean).join('\n') }]);
  }
  if (b.shareContent) attempts.push(['shareContent', { text, link }]);
  if (attempts.length === 0) return { ok: false, reason: 'no-share-method' };

  let lastError = null;
  for (const [method, params] of attempts) {
    try {
      await b[method](params);
      return { ok: true, method };
    } catch (err) {
      lastError = err;
      console.warn(`[MAX bridge] ${method} failed`, err);
    }
  }
  const reason = String(lastError?.message || lastError?.error || lastError || 'unknown').slice(0, 60);
  return { ok: false, reason };
}

/** Открывает внешнюю ссылку средствами MAX, если возможно. */
export function openExternal(url) {
  try {
    const b = bridge();
    if (b?.openLink) {
      b.openLink(url);
      return true;
    }
  } catch {}
  return false;
}
