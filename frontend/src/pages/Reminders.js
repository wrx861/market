import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { ArrowLeft, Bell, Plus, Check, Calendar, Gauge } from 'lucide-react';
import { showAlert } from '../utils/telegram';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Reminders = ({ userData, navigateTo, vehicleId }) => {
  const [reminders, setReminders] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadReminders();
  }, [vehicleId]);

  const loadReminders = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/garage/vehicle/${vehicleId}/reminders`);
      setReminders(response.data.reminders || []);
    } catch (error) {
      console.error('Error loading reminders:', error);
      showAlert('Ошибка загрузки напоминаний');
    } finally {
      setLoading(false);
    }
  };

  const handleComplete = async (reminderId) => {
    try {
      await axios.put(`${API}/garage/reminders/${reminderId}/complete`);
      showAlert('✅ Напоминание отмечено как выполненное');
      loadReminders();
    } catch (error) {
      console.error('Error completing reminder:', error);
      showAlert('Ошибка при обновлении');
    }
  };

  const handleEdit = (reminder) => {
    navigateTo('add-reminder', vehicleId, reminder);
  };

  const handleDelete = async (reminderId) => {
    if (!window.confirm('Удалить это напоминание?')) return;
    
    try {
      await axios.delete(`${API}/garage/reminders/${reminderId}`);
      showAlert('✅ Напоминание удалено');
      loadReminders();
    } catch (error) {
      console.error('Error deleting reminder:', error);
      showAlert('Ошибка удаления');
    }
  };

  const getReminderTypeLabel = (type) => {
    const labels = {
      'service': '🔧 Обслуживание',
      'insurance': '🛡️ Страховка',
      'inspection': '🔍 Техосмотр',
      'custom': '📌 Другое'
    };
    return labels[type] || type;
  };

  const activeReminders = reminders.filter(r => !r.is_completed);
  const completedReminders = reminders.filter(r => r.is_completed);

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-900 via-gray-800 to-gray-900 text-white pb-20">
      {/* Header */}
      <div className="bg-gradient-to-r from-gray-900 to-gray-800 p-6 shadow-2xl border-b-4 border-yellow-500">
        <button
          onClick={() => navigateTo('vehicle-detail', vehicleId)}
          className="flex items-center text-yellow-400 mb-4 hover:text-yellow-300"
        >
          <ArrowLeft size={20} className="mr-2" />
          Назад
        </button>
        
        <h1 className="text-2xl font-bold flex items-center">
          <Bell className="mr-3 text-yellow-400" size={28} />
          Напоминания
        </h1>
        <p className="text-gray-400 text-sm mt-1">
          {activeReminders.length} активных
        </p>
      </div>

      <div className="p-4">
        {/* Add Button */}
        <button
          onClick={() => navigateTo('add-reminder', vehicleId)}
          className="w-full bg-gradient-to-r from-yellow-500 to-orange-500 text-gray-900 py-4 px-6 rounded-xl flex items-center justify-center space-x-3 shadow-lg hover:shadow-xl transition mb-6 font-bold"
        >
          <Plus size={24} />
          <span>Создать напоминание</span>
        </button>

        {loading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-yellow-500 mx-auto mb-4"></div>
            <p className="text-gray-400">Загрузка...</p>
          </div>
        ) : (
          <>
            {/* Active Reminders */}
            <div className="mb-6">
              <h2 className="text-lg font-semibold mb-3 text-yellow-400 flex items-center">
                <Bell size={20} className="mr-2" />
                Активные ({activeReminders.length})
              </h2>
              
              {activeReminders.length === 0 ? (
                <div className="bg-gray-800 rounded-xl p-6 text-center border-2 border-dashed border-gray-600">
                  <Bell className="mx-auto mb-3 text-gray-600" size={48} />
                  <p className="text-gray-400">Нет активных напоминаний</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {activeReminders.map((reminder) => (
                    <div
                      key={reminder.id}
                      className="bg-gradient-to-r from-yellow-900 to-orange-900 bg-opacity-30 rounded-xl p-5 shadow-lg border-l-4 border-yellow-500"
                    >
                      <div className="flex justify-between items-start mb-3">
                        <div className="flex-1">
                          <p className="text-xs text-yellow-300 mb-1">
                            {getReminderTypeLabel(reminder.reminder_type)}
                          </p>
                          <p className="text-lg font-semibold">{reminder.title}</p>
                        </div>
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => handleComplete(reminder.id)}
                            className="bg-green-600 hover:bg-green-700 text-white p-2 rounded-lg transition"
                            title="Отметить выполненным"
                          >
                            <Check size={20} />
                          </button>
                          <div className="action-buttons">
                            <button onClick={() => handleEdit(reminder)} className="action-btn edit-btn" title="Редактировать">✏️</button>
                            <button onClick={() => handleDelete(reminder.id)} className="action-btn delete-btn" title="Удалить">🗑️</button>
                          </div>
                        </div>
                      </div>

                      {reminder.description && (
                        <p className="text-gray-300 text-sm mb-3">
                          {reminder.description}
                        </p>
                      )}

                      <div className="grid grid-cols-2 gap-2 text-sm">
                        {reminder.remind_at_date && (
                          <div className="bg-gray-900 bg-opacity-50 rounded-lg p-2 flex items-center space-x-2">
                            <Calendar size={16} className="text-yellow-400" />
                            <div>
                              <p className="text-gray-400 text-xs">Дата</p>
                              <p className="font-semibold">
                                {new Date(reminder.remind_at_date).toLocaleDateString('ru-RU')}
                              </p>
                            </div>
                          </div>
                        )}
                        
                        {reminder.remind_at_mileage && (
                          <div className="bg-gray-900 bg-opacity-50 rounded-lg p-2 flex items-center space-x-2">
                            <Gauge size={16} className="text-yellow-400" />
                            <div>
                              <p className="text-gray-400 text-xs">Пробег</p>
                              <p className="font-semibold">
                                {reminder.remind_at_mileage.toLocaleString('ru-RU')} км
                              </p>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Completed Reminders */}
            {completedReminders.length > 0 && (
              <div>
                <h2 className="text-lg font-semibold mb-3 text-gray-400 flex items-center">
                  <Check size={20} className="mr-2" />
                  Выполненные ({completedReminders.length})
                </h2>
                
                <div className="space-y-3">
                  {completedReminders.map((reminder) => (
                    <div
                      key={reminder.id}
                      className="bg-gray-800 bg-opacity-50 rounded-xl p-4 shadow border-l-4 border-gray-600"
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex-1">
                          <p className="text-xs text-gray-500 mb-1">
                            {getReminderTypeLabel(reminder.reminder_type)}
                          </p>
                          <p className="font-semibold text-gray-300 line-through">
                            {reminder.title}
                          </p>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="bg-green-600 text-white p-1 rounded">
                            <Check size={16} />
                          </span>
                          <button onClick={() => handleDelete(reminder.id)} className="action-btn delete-btn" title="Удалить">🗑️</button>
                        </div>
                      </div>
                      
                      {reminder.completed_at && (
                        <p className="text-xs text-gray-500">
                          Выполнено: {new Date(reminder.completed_at).toLocaleDateString('ru-RU')}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default Reminders;
