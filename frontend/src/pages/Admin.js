import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Activity, Users, ShoppingBag, TrendingUp, RefreshCw, ArrowLeft } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Admin = ({ navigateTo }) => {
  const [logs, setLogs] = useState([]);
  const [stats, setStats] = useState(null);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('activity'); // 'activity', 'users', 'stats', 'settings'
  const [settings, setSettings] = useState(null);
  const [markupPercent, setMarkupPercent] = useState(0);
  const [savingSettings, setSavingSettings] = useState(false);

  useEffect(() => {
    loadData();
  }, [activeTab]);

  const loadData = async () => {
    setLoading(true);
    try {
      if (activeTab === 'activity') {
        const response = await axios.get(`${API}/admin/activity?limit=50`);
        setLogs(response.data.logs || []);
      } else if (activeTab === 'users') {
        const response = await axios.get(`${API}/admin/users`);
        setUsers(response.data.users || []);
      } else if (activeTab === 'stats') {
        const response = await axios.get(`${API}/admin/stats`);
        setStats(response.data || null);
      } else if (activeTab === 'settings') {
        const response = await axios.get(`${API}/admin/settings`);
        setSettings(response.data.settings || null);
        setMarkupPercent(response.data.settings?.markup_percent || 0);
      }
    } catch (error) {
      console.error('Error loading admin data:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleString('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getActionLabel = (action) => {
    const labels = {
      'search_article': '🔍 Поиск по артикулу',
      'search_vin': '🚗 Поиск по VIN',
      'add_to_cart': '🛒 Добавление в корзину',
      'create_order': '📦 Создание заказа',
      'ai_search': '🤖 AI поиск',
      'update_markup': '💰 Изменение наценки'
    };
    return labels[action] || action;
  };

  const handleSaveMarkup = async () => {
    setSavingSettings(true);
    try {
      // Получаем telegram_id из Telegram WebApp
      const tg = window.Telegram?.WebApp;
      const telegram_id = tg?.initDataUnsafe?.user?.id || 508352361;

      await axios.post(`${API}/admin/settings`, {
        markup_percent: parseFloat(markupPercent),
        telegram_id: telegram_id
      });

      alert('✅ Наценка успешно обновлена!');
      loadData(); // Перезагружаем данные
    } catch (error) {
      console.error('Error saving settings:', error);
      alert('❌ Ошибка при сохранении настроек');
    } finally {
      setSavingSettings(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 pb-20">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 to-blue-600 text-white p-6">
        <button
          onClick={() => navigateTo('home')}
          className="flex items-center text-white mb-4 hover:text-purple-100"
        >
          <ArrowLeft size={20} className="mr-2" />
          Назад
        </button>
        <h1 className="text-2xl font-bold mb-2">👨‍💼 Админ-панель</h1>
        <p className="text-sm text-purple-100">Мониторинг активности</p>
      </div>

      {/* Tabs */}
      <div className="bg-white shadow-sm flex overflow-x-auto">
        <button
          onClick={() => setActiveTab('activity')}
          className={`flex-1 py-4 px-3 text-center font-semibold text-sm ${
            activeTab === 'activity'
              ? 'border-b-4 border-purple-600 text-purple-600'
              : 'text-gray-500'
          }`}
        >
          <Activity className="inline mr-1" size={16} />
          Активность
        </button>
        <button
          onClick={() => setActiveTab('users')}
          className={`flex-1 py-4 px-3 text-center font-semibold text-sm ${
            activeTab === 'users'
              ? 'border-b-4 border-purple-600 text-purple-600'
              : 'text-gray-500'
          }`}
        >
          <Users className="inline mr-1" size={16} />
          Пользователи
        </button>
        <button
          onClick={() => setActiveTab('stats')}
          className={`flex-1 py-4 px-3 text-center font-semibold text-sm ${
            activeTab === 'stats'
              ? 'border-b-4 border-purple-600 text-purple-600'
              : 'text-gray-500'
          }`}
        >
          <TrendingUp className="inline mr-1" size={16} />
          Статистика
        </button>
        <button
          onClick={() => setActiveTab('settings')}
          className={`flex-1 py-4 px-3 text-center font-semibold text-sm ${
            activeTab === 'settings'
              ? 'border-b-4 border-purple-600 text-purple-600'
              : 'text-gray-500'
          }`}
        >
          ⚙️ Настройки
        </button>
      </div>

      {/* Refresh Button */}
      <div className="p-4 bg-white border-b">
        <button
          onClick={loadData}
          disabled={loading}
          className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 transition flex items-center space-x-2"
        >
          <RefreshCw className={loading ? 'animate-spin' : ''} size={18} />
          <span>Обновить</span>
        </button>
      </div>

      {/* Content */}
      <div className="p-4">
        {loading ? (
          <div className="text-center py-12">
            <RefreshCw className="animate-spin mx-auto mb-4 text-purple-600" size={48} />
            <p className="text-gray-600">Загрузка...</p>
          </div>
        ) : (
          <>
            {/* Activity Tab */}
            {activeTab === 'activity' && (
              <div className="space-y-3">
                <h2 className="text-lg font-semibold mb-3">
                  Последние действия ({logs.length})
                </h2>
                {logs.map((log, index) => (
                  <div key={index} className="bg-white rounded-lg shadow p-4">
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <span className="font-semibold text-purple-600">
                          {getActionLabel(log.action)}
                        </span>
                        <p className="text-sm text-gray-600">
                          👤 {log.name || log.username || `ID: ${log.telegram_id}`}
                        </p>
                      </div>
                      <span className="text-xs text-gray-400">
                        {formatDate(log.timestamp)}
                      </span>
                    </div>
                    {log.details && Object.keys(log.details).length > 0 && (
                      <div className="mt-2 p-2 bg-gray-50 rounded text-xs">
                        <pre className="whitespace-pre-wrap">
                          {JSON.stringify(log.details, null, 2)}
                        </pre>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* Users Tab */}
            {activeTab === 'users' && (
              <div className="space-y-3">
                <h2 className="text-lg font-semibold mb-3">
                  Пользователи ({users.length})
                </h2>
                {users.map((user, index) => (
                  <div key={index} className="bg-white rounded-lg shadow p-4">
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="font-semibold">
                          {user.name || user.username || 'Без имени'}
                        </p>
                        <p className="text-sm text-gray-600">
                          @{user.username || 'anonymous'}
                        </p>
                        <p className="text-xs text-gray-400">
                          Telegram ID: {user.telegram_id}
                        </p>
                      </div>
                      <span className="text-xs text-gray-400">
                        {formatDate(user.created_at)}
                      </span>
                    </div>
                    {user.phone && (
                      <p className="text-sm text-gray-600 mt-2">
                        📞 {user.phone}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* Stats Tab */}
            {activeTab === 'stats' && stats && (
              <div className="space-y-4">
                {/* Stats Cards */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-white rounded-lg shadow p-4">
                    <Users className="text-blue-600 mb-2" size={24} />
                    <p className="text-2xl font-bold">{stats.stats?.total_users || 0}</p>
                    <p className="text-sm text-gray-600">Пользователей</p>
                  </div>
                  <div className="bg-white rounded-lg shadow p-4">
                    <ShoppingBag className="text-green-600 mb-2" size={24} />
                    <p className="text-2xl font-bold">{stats.stats?.total_orders || 0}</p>
                    <p className="text-sm text-gray-600">Заказов</p>
                  </div>
                  <div className="bg-white rounded-lg shadow p-4">
                    <TrendingUp className="text-purple-600 mb-2" size={24} />
                    <p className="text-2xl font-bold">
                      {(stats.stats?.total_revenue || 0).toLocaleString('ru-RU')} ₽
                    </p>
                    <p className="text-sm text-gray-600">Выручка</p>
                  </div>
                  <div className="bg-white rounded-lg shadow p-4">
                    <Activity className="text-orange-600 mb-2" size={24} />
                    <p className="text-2xl font-bold">{stats.stats?.total_searches || 0}</p>
                    <p className="text-sm text-gray-600">Поисков</p>
                  </div>
                </div>

                {/* Popular Queries */}
                <div className="bg-white rounded-lg shadow p-4">
                  <h3 className="font-semibold mb-3">Популярные запросы</h3>
                  <div className="space-y-2">
                    {stats.popular_queries?.map((query, index) => (
                      <div key={index} className="flex justify-between items-center">
                        <span className="text-gray-800">{query._id}</span>
                        <span className="bg-purple-100 text-purple-800 px-2 py-1 rounded text-sm">
                          {query.count}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Settings Tab */}
            {activeTab === 'settings' && (
              <div className="space-y-4">
                <h2 className="text-lg font-semibold mb-3">Настройки системы</h2>
                
                {/* Markup Settings */}
                <div className="bg-white rounded-lg shadow p-6">
                  <h3 className="font-semibold mb-4 flex items-center">
                    <span className="text-2xl mr-2">💰</span>
                    Наценка на товары
                  </h3>
                  <p className="text-sm text-gray-600 mb-4">
                    Установите процент наценки, который будет добавляться к ценам поставщика
                  </p>
                  
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Процент наценки (%)
                      </label>
                      <input
                        type="number"
                        min="0"
                        max="100"
                        step="0.1"
                        value={markupPercent}
                        onChange={(e) => setMarkupPercent(e.target.value)}
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-600"
                        placeholder="Например: 15"
                      />
                      <p className="text-xs text-gray-500 mt-1">
                        Текущая наценка: {markupPercent}%
                      </p>
                    </div>

                    {/* Example */}
                    <div className="bg-blue-50 p-4 rounded-lg">
                      <p className="text-sm font-semibold text-blue-800 mb-2">📊 Пример:</p>
                      <div className="text-sm text-gray-700 space-y-1">
                        <p>Цена поставщика: 1000 ₽</p>
                        <p>Наценка {markupPercent}%: +{(1000 * markupPercent / 100).toFixed(0)} ₽</p>
                        <p className="font-bold text-green-700">
                          Итоговая цена: {Math.ceil(1000 * (1 + markupPercent / 100))} ₽
                        </p>
                      </div>
                    </div>

                    <button
                      onClick={handleSaveMarkup}
                      disabled={savingSettings}
                      className="w-full bg-purple-600 text-white py-3 rounded-lg font-semibold hover:bg-purple-700 transition disabled:opacity-50"
                    >
                      {savingSettings ? '💾 Сохранение...' : '💾 Сохранить наценку'}
                    </button>
                  </div>
                </div>

                {/* Info */}
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                  <p className="text-sm text-yellow-800">
                    ⚠️ <strong>Внимание:</strong> Изменение наценки повлияет на все будущие поиски.
                    Цены в уже созданных заказах останутся прежними.
                  </p>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default Admin;
