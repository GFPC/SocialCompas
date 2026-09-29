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

/** Делится текстом через диалог MAX (в чат MAX / нативный share). Возвращает true, если мост обработал вызов. */
export function shareViaMax({ text, link }) {
  const b = bridge();
  try {
    if (b?.shareMaxContent) {
      b.shareMaxContent({ text, link });
      return true;
    }
    if (b?.shareContent) {
      b.shareContent({ text, link });
      return true;
    }
  } catch {}
  return false;
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
