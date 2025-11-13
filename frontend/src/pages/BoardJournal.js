import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { ArrowLeft, FileText, Plus, Fuel, Navigation, DollarSign, AlertCircle } from 'lucide-react';
import { showAlert } from '../utils/telegram';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const BoardJournal = ({ userData, navigateTo, vehicleId }) => {
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    loadLogEntries();
  }, [vehicleId]);

  const loadLogEntries = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/garage/vehicle/${vehicleId}/log`);
      setEntries(response.data.entries || []);
    } catch (error) {
      console.error('Error loading log entries:', error);
      showAlert('Ошибка загрузки бортжурнала');
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = (entry) => {
    navigateTo('add-log', vehicleId, entry);
  };

  const handleDelete = async (entryId) => {
    if (!window.confirm('Удалить эту запись?')) return;
    
    try {
      await axios.delete(`${API}/garage/log/${entryId}`);
      showAlert('✅ Запись удалена');
      loadLogEntries();
    } catch (error) {
      console.error('Error deleting entry:', error);
      showAlert('Ошибка удаления');
    }
  };

  const getFilteredEntries = () => {
    if (filter === 'all') return entries;
    return entries.filter(entry => entry.entry_type === filter);
  };

  const getEntryIcon = (type) => {
    const icons = {
      'refuel': { icon: <Fuel size={20} />, color: 'text-orange-400', bg: 'bg-orange-900' },
      'trip': { icon: <Navigation size={20} />, color: 'text-blue-400', bg: 'bg-blue-900' },
      'expense': { icon: <DollarSign size={20} />, color: 'text-green-400', bg: 'bg-green-900' },
      'diagnostic': { icon: <AlertCircle size={20} />, color: 'text-red-400', bg: 'bg-red-900' },
      'note': { icon: <FileText size={20} />, color: 'text-purple-400', bg: 'bg-purple-900' }
    };
    return icons[type] || icons['note'];
  };

  const getEntryTypeLabel = (type) => {
    const labels = {
      'refuel': '⛽ Заправка',
      'trip': '🗺️ Поездка',
      'expense': '💰 Расход',
      'diagnostic': '⚠️ Диагностика',
      'note': '📝 Заметка'
    };
    return labels[type] || type;
  };

  const filteredEntries = getFilteredEntries();

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-900 via-gray-800 to-gray-900 text-white pb-20">
      <div className="bg-gradient-to-r from-gray-900 to-gray-800 p-6 shadow-2xl border-b-4 border-green-500">
        <button
          onClick={() => navigateTo('vehicle-detail', vehicleId)}
          className="flex items-center text-green-400 mb-4 hover:text-green-300"
        >
          <ArrowLeft size={20} className="mr-2" />
          Назад
        </button>
        
        <h1 className="text-2xl font-bold flex items-center">
          <FileText className="mr-3 text-green-400" size={28} />
          Бортжурнал
        </h1>
      </div>

      <div className="p-4">
        <div className="flex overflow-x-auto gap-2 mb-6 pb-2">
          {[
            { key: 'all', label: 'Все', icon: '📋' },
            { key: 'refuel', label: 'Заправки', icon: '⛽' },
            { key: 'trip', label: 'Поездки', icon: '🗺️' },
            { key: 'expense', label: 'Расходы', icon: '💰' },
            { key: 'diagnostic', label: 'Диагностика', icon: '⚠️' }
          ].map(({ key, label, icon }) => (
            <button
              key={key}
              onClick={() => setFilter(key)}
              className={`px-4 py-2 rounded-lg whitespace-nowrap transition ${
                filter === key
                  ? 'bg-green-600 text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              {icon} {label}
            </button>
          ))}
        </div>

        <button
          onClick={() => navigateTo('add-log', vehicleId)}
          className="w-full bg-gradient-to-r from-green-500 to-green-600 text-white py-4 px-6 rounded-xl flex items-center justify-center space-x-3 shadow-lg hover:shadow-xl transition mb-6"
        >
          <Plus size={24} />
          <span className="font-semibold">Добавить запись</span>
        </button>

        {loading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-500 mx-auto mb-4"></div>
            <p className="text-gray-400">Загрузка...</p>
          </div>
        ) : filteredEntries.length === 0 ? (
          <div className="bg-gray-800 rounded-xl p-8 text-center border-2 border-dashed border-gray-600">
            <FileText className="mx-auto mb-4 text-gray-600" size={64} />
            <h3 className="text-xl font-semibold mb-2 text-gray-300">
              {filter === 'all' ? 'Журнал пуст' : 'Нет записей этого типа'}
            </h3>
            <p className="text-gray-500 mb-4">Добавьте первую запись</p>
          </div>
        ) : (
          <div className="space-y-3">
            {filteredEntries.map((entry, index) => {
              const iconData = getEntryIcon(entry.entry_type);
              return (
                <div
                  key={entry.id || index}
                  className="bg-gradient-to-r from-gray-800 to-gray-700 rounded-xl p-5 shadow-lg border-l-4 border-green-500"
                >
                  <div className="flex justify-between items-start mb-3">
                    <div className="flex items-start gap-3 flex-1">
                      <div className={`${iconData.bg} p-2 rounded-lg ${iconData.color}`}>
                        {iconData.icon}
                      </div>
                      <div className="flex-1">
                        <p className="text-lg font-semibold mb-1">
                          {getEntryTypeLabel(entry.entry_type)}
                        </p>
                        <p className="text-gray-400 text-sm">{entry.title}</p>
                      </div>
                    </div>
                    <div className="action-buttons">
                      <button onClick={() => handleEdit(entry)} className="action-btn edit-btn" title="Редактировать">✏️</button>
                      <button onClick={() => handleDelete(entry.id)} className="action-btn delete-btn" title="Удалить">🗑️</button>
                    </div>
                  </div>

                  {entry.description && (
                    <p className="text-gray-400 text-sm mb-3 border-l-2 border-gray-600 pl-3">
                      {entry.description}
                    </p>
                  )}

                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div className="bg-gray-900 rounded-lg p-2">
                      <p className="text-gray-500 text-xs">Дата</p>
                      <p className="font-semibold">
                        {new Date(entry.entry_date).toLocaleDateString('ru-RU')}
                      </p>
                    </div>
                    
                    {entry.mileage && (
                      <div className="bg-gray-900 rounded-lg p-2">
                        <p className="text-gray-500 text-xs">Пробег</p>
                        <p className="font-semibold">{entry.mileage.toLocaleString('ru-RU')} км</p>
                      </div>
                    )}
                  </div>

                  {entry.entry_type === 'refuel' && (
                    <div className="mt-2 grid grid-cols-2 gap-2">
                      {entry.fuel_amount && (
                        <div className="bg-gray-900 rounded-lg p-2">
                          <p className="text-gray-500 text-xs">Объем</p>
                          <p className="font-semibold">{entry.fuel_amount} л</p>
                        </div>
                      )}
                      {entry.fuel_cost && (
                        <div className="bg-gray-900 rounded-lg p-2">
                          <p className="text-gray-500 text-xs">Стоимость</p>
                          <p className="font-semibold">{entry.fuel_cost.toLocaleString('ru-RU')} ₽</p>
                        </div>
                      )}
                    </div>
                  )}

                  {entry.entry_type === 'trip' && entry.trip_distance && (
                    <div className="mt-2 bg-gray-900 rounded-lg p-2">
                      <p className="text-gray-500 text-xs">Расстояние</p>
                      <p className="font-semibold">{entry.trip_distance} км</p>
                    </div>
                  )}

                  {entry.entry_type === 'expense' && entry.expense_amount && (
                    <div className="mt-2 bg-gray-900 rounded-lg p-2">
                      <p className="text-gray-500 text-xs">Сумма</p>
                      <p className="font-semibold">{entry.expense_amount.toLocaleString('ru-RU')} ₽</p>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default BoardJournal;
