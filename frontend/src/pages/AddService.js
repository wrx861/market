import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { ArrowLeft, Save, Loader2 } from 'lucide-react';
import { showAlert } from '../utils/telegram';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AddService = ({ userData, navigateTo, vehicleId, editData }) => {
  const [vehicle, setVehicle] = useState(null);
  const [formData, setFormData] = useState({
    service_type: 'general_maintenance',
    title: '',
    description: '',
    mileage: 0,
    cost: 0,
    service_date: new Date().toISOString().split('T')[0],
    service_provider: '',
    parts_used: ''
  });
  const [saving, setSaving] = useState(false);
  const isEditMode = !!editData;

  useEffect(() => {
    loadVehicle();
    if (editData) {
      // Предзаполняем форму при редактировании
      setFormData({
        service_type: editData.service_type || 'general_maintenance',
        title: editData.title || '',
        description: editData.description || '',
        mileage: editData.mileage || 0,
        cost: editData.cost || 0,
        service_date: editData.service_date ? editData.service_date.split('T')[0] : new Date().toISOString().split('T')[0],
        service_provider: editData.service_provider || '',
        parts_used: editData.parts_used ? editData.parts_used.join(', ') : ''
      });
    }
  }, [vehicleId, editData]);

  const loadVehicle = async () => {
    try {
      const response = await axios.get(`${API}/garage/vehicle/${vehicleId}`);
      const vehicleData = response.data.vehicle;
      setVehicle(vehicleData);
      setFormData(prev => ({ ...prev, mileage: vehicleData.mileage }));
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
      showAlert('Введите название работы');
      return;
    }

    setSaving(true);
    try {
      // Преобразуем parts_used из строки в массив
      const parts = formData.parts_used
        ? formData.parts_used.split(',').map(p => p.trim()).filter(p => p)
        : null;

      if (isEditMode) {
        // Режим редактирования - PUT запрос
        await axios.put(`${API}/garage/service/${editData.id}`, {
          ...formData,
          parts_used: parts
        });
        showAlert('✅ Запись обновлена');
      } else {
        // Режим создания - POST запрос
        await axios.post(`${API}/garage/vehicle/${vehicleId}/service`, {
          ...formData,
          telegram_id: userData.telegram_id,
          mileage: parseInt(formData.mileage),
          cost: parseFloat(formData.cost),
          parts_used: parts
        });
        showAlert('✅ Запись об обслуживании добавлена!');
      }
      
      navigateTo('service-log', vehicleId);
    } catch (error) {
      console.error('Error adding service:', error);
      showAlert('Ошибка при добавлении записи');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-900 via-gray-800 to-gray-900 text-white pb-20">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-900 to-blue-800 p-6 shadow-2xl border-b-4 border-blue-500">
        <button
          onClick={() => navigateTo('vehicle-detail', vehicleId)}
          className="flex items-center text-blue-300 mb-4 hover:text-blue-200"
        >
          <ArrowLeft size={20} className="mr-2" />
          Назад
        </button>
        
        <h1 className="text-2xl font-bold">
          {isEditMode ? 'Редактировать обслуживание' : 'Добавить обслуживание'}
        </h1>
        {vehicle && (
          <p className="text-blue-200 text-sm mt-1">
            {vehicle.make} {vehicle.model} ({vehicle.year})
          </p>
        )}
      </div>

      <form onSubmit={handleSubmit} className="p-4 space-y-4">
        {/* Service Type */}
        <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
          <label className="block text-sm font-semibold text-gray-300 mb-2">
            Тип обслуживания <span className="text-red-500">*</span>
          </label>
          <select
            name="service_type"
            value={formData.service_type}
            onChange={handleChange}
            className="w-full bg-gray-900 text-white px-4 py-3 rounded-lg border border-gray-700 focus:outline-none focus:border-blue-500"
          >
            <option value="oil_change">🛢️ Замена масла</option>
            <option value="tire_change">🛞 Замена шин</option>
            <option value="brake_service">🔴 Обслуживание тормозов</option>
            <option value="general_maintenance">🔧 Общее ТО</option>
            <option value="repair">⚙️ Ремонт</option>
            <option value="other">📋 Другое</option>
          </select>
        </div>

        {/* Title */}
        <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
          <label className="block text-sm font-semibold text-gray-300 mb-2">
            Название работы <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            name="title"
            value={formData.title}
            onChange={handleChange}
            placeholder="Например: Замена моторного масла 5W-40"
            className="w-full bg-gray-900 text-white px-4 py-3 rounded-lg border border-gray-700 focus:outline-none focus:border-blue-500"
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
            placeholder="Детали работы..."
            rows="3"
            className="w-full bg-gray-900 text-white px-4 py-3 rounded-lg border border-gray-700 focus:outline-none focus:border-blue-500"
          />
        </div>

        {/* Mileage */}
        <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
          <label className="block text-sm font-semibold text-gray-300 mb-2">
            Пробег (км) <span className="text-red-500">*</span>
          </label>
          <input
            type="number"
            name="mileage"
            value={formData.mileage}
            onChange={handleChange}
            min="0"
            className="w-full bg-gray-900 text-white px-4 py-3 rounded-lg border border-gray-700 focus:outline-none focus:border-blue-500"
            required
          />
        </div>

        {/* Cost */}
        <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
          <label className="block text-sm font-semibold text-gray-300 mb-2">
            Стоимость (₽)
          </label>
          <input
            type="number"
            name="cost"
            value={formData.cost}
            onChange={handleChange}
            min="0"
            step="0.01"
            placeholder="0"
            className="w-full bg-gray-900 text-white px-4 py-3 rounded-lg border border-gray-700 focus:outline-none focus:border-blue-500"
          />
        </div>

        {/* Service Date */}
        <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
          <label className="block text-sm font-semibold text-gray-300 mb-2">
            Дата обслуживания <span className="text-red-500">*</span>
          </label>
          <input
            type="date"
            name="service_date"
            value={formData.service_date}
            onChange={handleChange}
            className="w-full bg-gray-900 text-white px-4 py-3 rounded-lg border border-gray-700 focus:outline-none focus:border-blue-500"
            required
          />
        </div>

        {/* Service Provider */}
        <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
          <label className="block text-sm font-semibold text-gray-300 mb-2">
            Исполнитель
          </label>
          <input
            type="text"
            name="service_provider"
            value={formData.service_provider}
            onChange={handleChange}
            placeholder="СТО или Самостоятельно"
            className="w-full bg-gray-900 text-white px-4 py-3 rounded-lg border border-gray-700 focus:outline-none focus:border-blue-500"
          />
        </div>

        {/* Parts Used */}
        <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
          <label className="block text-sm font-semibold text-gray-300 mb-2">
            Использованные запчасти
          </label>
          <input
            type="text"
            name="parts_used"
            value={formData.parts_used}
            onChange={handleChange}
            placeholder="Через запятую: Масло 5W-40, Фильтр масляный, Прокладка"
            className="w-full bg-gray-900 text-white px-4 py-3 rounded-lg border border-gray-700 focus:outline-none focus:border-blue-500"
          />
          <p className="text-xs text-gray-500 mt-1">
            Укажите запчасти через запятую
          </p>
        </div>

        {/* Submit */}
        <button
          type="submit"
          disabled={saving}
          className="w-full bg-gradient-to-r from-blue-500 to-blue-600 text-white py-4 px-6 rounded-xl shadow-lg hover:shadow-xl transition disabled:opacity-50 flex items-center justify-center space-x-3 font-bold"
        >
          {saving ? (
            <>
              <Loader2 className="animate-spin" size={24} />
              <span>Сохранение...</span>
            </>
          ) : (
            <>
              <Save size={24} />
              <span>Сохранить</span>
            </>
          )}
        </button>
      </form>
    </div>
  );
};

export default AddService;
