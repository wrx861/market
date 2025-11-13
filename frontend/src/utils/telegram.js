import WebApp from '@twa-dev/sdk';

// Проверка, запущено ли приложение в Telegram
export const isTelegramWebApp = () => {
  return WebApp.initData !== '';
};

// Безопасный wrapper для showAlert
export const showAlert = (message, callback) => {
  if (isTelegramWebApp() && WebApp.showAlert) {
    WebApp.showAlert(message, callback);
  } else {
    // Fallback для браузера
    window.alert(message);
    if (callback) callback();
  }
};

// Безопасный wrapper для showConfirm
export const showConfirm = (message, callback) => {
  if (isTelegramWebApp() && WebApp.showConfirm) {
    WebApp.showConfirm(message, callback);
  } else {
    // Fallback для браузера
    const result = window.confirm(message);
    if (callback) callback(result);
  }
};

// Безопасный wrapper для showPopup
export const showPopup = (params, callback) => {
  if (isTelegramWebApp() && WebApp.showPopup) {
    WebApp.showPopup(params, callback);
  } else {
    // Fallback для браузера
    window.alert(params.message || params.title);
    if (callback) callback();
  }
};

// Получение данных пользователя
export const getUserData = () => {
  if (isTelegramWebApp() && WebApp.initDataUnsafe?.user) {
    const tgUser = WebApp.initDataUnsafe.user;
    return {
      telegram_id: tgUser.id,
      username: tgUser.username,
      name: `${tgUser.first_name || ''} ${tgUser.last_name || ''}`.trim(),
    };
  } else {
    // Тестовый пользователь для preview
    return {
      telegram_id: 123456789,
      username: 'testuser',
      name: 'Test User (Preview Mode)',
    };
  }
};

// Инициализация WebApp
export const initWebApp = () => {
  if (isTelegramWebApp()) {
    WebApp.ready();
    WebApp.expand();
  } else {
    console.log('Running in browser preview mode');
  }
};

// BackButton управление
export const BackButton = {
  show: () => {
    if (isTelegramWebApp() && WebApp.BackButton) {
      WebApp.BackButton.show();
    }
  },
  hide: () => {
    if (isTelegramWebApp() && WebApp.BackButton) {
      WebApp.BackButton.hide();
    }
  },
  onClick: (callback) => {
    if (isTelegramWebApp() && WebApp.BackButton) {
      WebApp.BackButton.onClick(callback);
    }
  }
};

export default {
  isTelegramWebApp,
  showAlert,
  showConfirm,
  showPopup,
  getUserData,
  initWebApp,
  BackButton
};
