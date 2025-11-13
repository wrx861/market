import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { ArrowLeft, Save, Loader2 } from 'lucide-react';
import { showAlert } from '../utils/telegram';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AddReminder = ({ userData, navigateTo, vehicleId, editData }) => {
  const [vehicle, setVehicle] = useState(null);
  const [formData, setFormData] = useState({
    reminder_type: 'service',
    title: '',
    description: '',
    remind_at_date: '',
    remind_at_mileage: ''
  });
  const [saving, setSaving] = useState(false);
  const isEditMode = !!editData;

  useEffect(() => {
    loadVehicle();
    if (editData) {
      setFormData({
        reminder_type: editData.reminder_type || 'service',
        title: editData.title || '',
        description: editData.description || '',
        remind_at_date: editData.remind_at_date ? editData.remind_at_date.split('T')[0] : '',
        remind_at_mileage: editData.remind_at_mileage || ''
      });
    }
  }, [vehicleId, editData]);

  const loadVehicle = async () => {
    try {
      const response = await axios.get(`${API}/garage/vehicle/${vehicleId}`);
      setVehicle(response.data.vehicle);
    } catch (error) {
      console.error('Error loading vehicle:', error);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!formData.title.trim()) {
      showAlert('Введите название напоминания');
      return;
    }

    if (!formData.remind_at_date && !formData.remind_at_mileage) {
      showAlert('Укажите дату или пробег для напоминания');
      return;
    }

    setSaving(true);
    try {
      const payload = {
        reminder_type: formData.reminder_type,
        title: formData.title,
        description: formData.description || null,
        remind_at_date: formData.remind_at_date || null,
        remind_at_mileage: formData.remind_at_mileage ? parseInt(formData.remind_at_mileage) : null
      };

      if (isEditMode) {
        // Режим редактирования - PUT запрос
        await axios.put(`${API}/garage/reminders/${editData.id}`, payload);
        showAlert('✅ Напоминание обновлено');
      } else {
        // Режим создания - POST запрос
        await axios.post(`${API}/garage/vehicle/${vehicleId}/reminders`, {
          telegram_id: userData.telegram_id,
          ...payload
        });
        showAlert('✅ Напоминание создано!');
      }

      navigateTo('reminders', vehicleId);
    } catch (error) {
      console.error('Error adding reminder:', error);
      showAlert('Ошибка при создании напоминания');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-900 via-gray-800 to-gray-900 text-white pb-20">
      {/* Header */}
      <div className="bg-gradient-to-r from-yellow-900 to-orange-900 p-6 shadow-2xl border-b-4 border-yellow-500">
        <button
          onClick={() => navigateTo('vehicle-detail', vehicleId)}
          className="flex items-center text-yellow-300 mb-4 hover:text-yellow-200"
        >
          <ArrowLeft size={20} className="mr-2" />
          Назад
        </button>
        
        <h1 className="text-2xl font-bold">
          {isEditMode ? 'Редактировать напоминание' : 'Создать напоминание'}
        </h1>
        {vehicle && (
          <p className="text-yellow-200 text-sm mt-1">
            {vehicle.make} {vehicle.model} ({vehicle.year})
          </p>
        )}
      </div>

      <form onSubmit={handleSubmit} className="p-4 space-y-4">
        {/* Reminder Type */}
        <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
          <label className="block text-sm font-semibold text-gray-300 mb-2">
            Тип напоминания <span className="text-red-500">*</span>
          </label>
          <select
            name="reminder_type"
            value={formData.reminder_type}
            onChange={handleChange}
            className="w-full bg-gray-900 text-white px-4 py-3 rounded-lg border border-gray-700 focus:outline-none focus:border-yellow-500"
          >
            <option value="service">🔧 Обслуживание</option>
            <option value="insurance">🛡️ Страховка</option>
            <option value="inspection">🔍 Техосмотр</option>
            <option value="custom">📌 Другое</option>
          </select>
        </div>

        {/* Title */}
        <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
          <label className="block text-sm font-semibold text-gray-300 mb-2">
            Название <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            name="title"
            value={formData.title}
            onChange={handleChange}
            placeholder="Например: Замена масла"
            className="w-full bg-gray-900 text-white px-4 py-3 rounded-lg border border-gray-700 focus:outline-none focus:border-yellow-500"
            required
          />
        </div>

        {/* Description */}
        <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
          <label className="block text-sm font-semibold text-gray-300 mb-2">
            Описание
          </label>
          <textarea
            name="description"
            value={formData.description}
            onChange={handleChange}
            placeholder="Дополнительная информация..."
            rows="3"
            className="w-full bg-gray-900 text-white px-4 py-3 rounded-lg border border-gray-700 focus:outline-none focus:border-yellow-500"
          />
        </div>

        {/* Info */}
        <div className="bg-blue-900 bg-opacity-30 border border-blue-500 rounded-xl p-4">
          <p className="text-blue-300 text-sm">
            💡 Укажите дату и/или пробег. Напоминание сработает при достижении любого из условий.
          </p>
        </div>

        {/* Remind at Date */}
        <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
          <label className="block text-sm font-semibold text-gray-300 mb-2">
            📅 Напомнить по дате
          </label>
          <input
            type="date"
            name="remind_at_date"
            value={formData.remind_at_date}
            onChange={handleChange}
            min={new Date().toISOString().split('T')[0]}
            className="w-full bg-gray-900 text-white px-4 py-3 rounded-lg border border-gray-700 focus:outline-none focus:border-yellow-500"
          />
        </div>

        {/* Remind at Mileage */}
        <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
          <label className="block text-sm font-semibold text-gray-300 mb-2">
            📏 Напомнить при пробеге (км)
          </label>
          <input
            type="number"
            name="remind_at_mileage"
            value={formData.remind_at_mileage}
            onChange={handleChange}
            min="0"
            placeholder={vehicle ? `Текущий: ${vehicle.mileage} км` : ''}
            className="w-full bg-gray-900 text-white px-4 py-3 rounded-lg border border-gray-700 focus:outline-none focus:border-yellow-500"
          />
          {vehicle && formData.remind_at_mileage && parseInt(formData.remind_at_mileage) > vehicle.mileage && (
            <p className="text-xs text-gray-400 mt-1">
              Осталось: {(parseInt(formData.remind_at_mileage) - vehicle.mileage).toLocaleString('ru-RU')} км
            </p>
          )}
        </div>

        {/* Submit */}
        <button
          type="submit"
          disabled={saving}
          className="w-full bg-gradient-to-r from-yellow-500 to-orange-500 text-gray-900 py-4 px-6 rounded-xl shadow-lg hover:shadow-xl transition disabled:opacity-50 flex items-center justify-center space-x-3 font-bold"
        >
          {saving ? (
            <>
              <Loader2 className="animate-spin" size={24} />
              <span>Создание...</span>
            </>
          ) : (
            <>
              <Save size={24} />
              <span>Создать напоминание</span>
            </>
          )}
        </button>
      </form>
    </div>
  );
};

export default AddReminder;
