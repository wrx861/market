import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { ArrowLeft, Save, Loader2 } from 'lucide-react';
import { showAlert } from '../utils/telegram';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AddLog = ({ userData, navigateTo, vehicleId, editData }) => {
  const [vehicle, setVehicle] = useState(null);
  const [entryType, setEntryType] = useState(editData?.entry_type || 'note');
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    mileage: 0,
    entry_date: new Date().toISOString().split('T')[0],
    // Refuel fields
    fuel_amount: '',
    fuel_cost: '',
    fuel_type: 'АИ-95',
    // Trip fields
    trip_distance: '',
    trip_purpose: '',
    // Expense fields
    expense_amount: '',
    expense_category: 'other'
  });
  const [saving, setSaving] = useState(false);
  const isEditMode = !!editData;

  useEffect(() => {
    loadVehicle();
    if (editData) {
      setEntryType(editData.entry_type || 'note');
      setFormData({
        title: editData.title || '',
        description: editData.description || '',
        mileage: editData.mileage || 0,
        entry_date: editData.entry_date ? editData.entry_date.split('T')[0] : new Date().toISOString().split('T')[0],
        fuel_amount: editData.fuel_amount || '',
        fuel_cost: editData.fuel_cost || '',
        fuel_type: editData.fuel_type || 'АИ-95',
        trip_distance: editData.trip_distance || '',
        trip_purpose: editData.trip_purpose || '',
        expense_amount: editData.expense_amount || '',
        expense_category: editData.expense_category || 'other'
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
      showAlert('Введите название записи');
      return;
    }

    setSaving(true);
    try {
      const payload = {
        telegram_id: userData.telegram_id,
        entry_type: entryType,
        title: formData.title,
        description: formData.description || null,
        mileage: parseInt(formData.mileage),
        entry_date: formData.entry_date,
        // Добавляем поля в зависимости от типа
        ...(entryType === 'refuel' && {
          fuel_amount: formData.fuel_amount ? parseFloat(formData.fuel_amount) : null,
          fuel_cost: formData.fuel_cost ? parseFloat(formData.fuel_cost) : null,
          fuel_type: formData.fuel_type
        }),
        ...(entryType === 'trip' && {
          trip_distance: formData.trip_distance ? parseInt(formData.trip_distance) : null,
          trip_purpose: formData.trip_purpose || null
        }),
        ...(entryType === 'expense' && {
          expense_amount: formData.expense_amount ? parseFloat(formData.expense_amount) : null,
          expense_category: formData.expense_category
        })
      };

      if (isEditMode) {
        // Режим редактирования - PUT запрос (без telegram_id)
        const { telegram_id, ...updatePayload } = payload;
        await axios.put(`${API}/garage/log/${editData.id}`, updatePayload);
        showAlert('✅ Запись обновлена');
      } else {
        // Режим создания - POST запрос
        await axios.post(`${API}/garage/vehicle/${vehicleId}/log`, payload);
        showAlert('✅ Запись добавлена в бортжурнал!');
      }
      
      navigateTo('board-journal', vehicleId);
    } catch (error) {
      console.error('Error adding log:', error);
      showAlert('Ошибка при добавлении записи');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-900 via-gray-800 to-gray-900 text-white pb-20">
      {/* Header */}
      <div className="bg-gradient-to-r from-green-900 to-green-800 p-6 shadow-2xl border-b-4 border-green-500">
        <button
          onClick={() => navigateTo('vehicle-detail', vehicleId)}
          className="flex items-center text-green-300 mb-4 hover:text-green-200"
        >
          <ArrowLeft size={20} className="mr-2" />
          Назад
        </button>
        
        <h1 className="text-2xl font-bold">
          {isEditMode ? 'Редактировать запись' : 'Добавить запись'}
        </h1>
        {vehicle && (
          <p className="text-green-200 text-sm mt-1">
            {vehicle.make} {vehicle.model} ({vehicle.year})
          </p>
        )}
      </div>

      <form onSubmit={handleSubmit} className="p-4 space-y-4">
        {/* Entry Type */}
        <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
          <label className="block text-sm font-semibold text-gray-300 mb-2">
            Тип записи <span className="text-red-500">*</span>
          </label>
          <select
            value={entryType}
            onChange={(e) => setEntryType(e.target.value)}
            className="w-full bg-gray-900 text-white px-4 py-3 rounded-lg border border-gray-700 focus:outline-none focus:border-green-500"
          >
            <option value="note">📝 Заметка</option>
            <option value="refuel">⛽ Заправка</option>
            <option value="trip">🗺️ Поездка</option>
            <option value="expense">💰 Расход</option>
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
            placeholder="Например: Заправка на Shell"
            className="w-full bg-gray-900 text-white px-4 py-3 rounded-lg border border-gray-700 focus:outline-none focus:border-green-500"
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
            className="w-full bg-gray-900 text-white px-4 py-3 rounded-lg border border-gray-700 focus:outline-none focus:border-green-500"
          />
        </div>

        {/* Specific Fields Based on Type */}
        {entryType === 'refuel' && (
          <>
            <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
              <label className="block text-sm font-semibold text-gray-300 mb-2">
                Количество литров
              </label>
              <input
                type="number"
                name="fuel_amount"
                value={formData.fuel_amount}
                onChange={handleChange}
                step="0.01"
                placeholder="45.5"
                className="w-full bg-gray-900 text-white px-4 py-3 rounded-lg border border-gray-700 focus:outline-none focus:border-green-500"
              />
            </div>

            <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
              <label className="block text-sm font-semibold text-gray-300 mb-2">
                Стоимость (₽)
              </label>
              <input
                type="number"
                name="fuel_cost"
                value={formData.fuel_cost}
                onChange={handleChange}
                step="0.01"
                placeholder="2500"
                className="w-full bg-gray-900 text-white px-4 py-3 rounded-lg border border-gray-700 focus:outline-none focus:border-green-500"
              />
            </div>

            <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
              <label className="block text-sm font-semibold text-gray-300 mb-2">
                Тип топлива
              </label>
              <select
                name="fuel_type"
                value={formData.fuel_type}
                onChange={handleChange}
                className="w-full bg-gray-900 text-white px-4 py-3 rounded-lg border border-gray-700 focus:outline-none focus:border-green-500"
              >
                <option value="АИ-92">АИ-92</option>
                <option value="АИ-95">АИ-95</option>
                <option value="АИ-98">АИ-98</option>
                <option value="АИ-100">АИ-100</option>
                <option value="Дизель">Дизель</option>
                <option value="Газ">Газ</option>
              </select>
            </div>
          </>
        )}

        {entryType === 'trip' && (
          <>
            <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
              <label className="block text-sm font-semibold text-gray-300 mb-2">
                Расстояние (км)
              </label>
              <input
                type="number"
                name="trip_distance"
                value={formData.trip_distance}
                onChange={handleChange}
                placeholder="150"
                className="w-full bg-gray-900 text-white px-4 py-3 rounded-lg border border-gray-700 focus:outline-none focus:border-green-500"
              />
            </div>

            <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
              <label className="block text-sm font-semibold text-gray-300 mb-2">
                Цель поездки
              </label>
              <input
                type="text"
                name="trip_purpose"
                value={formData.trip_purpose}
                onChange={handleChange}
                placeholder="Поездка на работу, отпуск..."
                className="w-full bg-gray-900 text-white px-4 py-3 rounded-lg border border-gray-700 focus:outline-none focus:border-green-500"
              />
            </div>
          </>
        )}

        {entryType === 'expense' && (
          <>
            <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
              <label className="block text-sm font-semibold text-gray-300 mb-2">
                Сумма (₽)
              </label>
              <input
                type="number"
                name="expense_amount"
                value={formData.expense_amount}
                onChange={handleChange}
                step="0.01"
                placeholder="1500"
                className="w-full bg-gray-900 text-white px-4 py-3 rounded-lg border border-gray-700 focus:outline-none focus:border-green-500"
              />
            </div>

            <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
              <label className="block text-sm font-semibold text-gray-300 mb-2">
                Категория расхода
              </label>
              <select
                name="expense_category"
                value={formData.expense_category}
                onChange={handleChange}
                className="w-full bg-gray-900 text-white px-4 py-3 rounded-lg border border-gray-700 focus:outline-none focus:border-green-500"
              >
                <option value="fuel">⛽ Топливо</option>
                <option value="service">🔧 Обслуживание</option>
                <option value="parking">🅿️ Парковка</option>
                <option value="fines">🚫 Штрафы</option>
                <option value="insurance">🛡️ Страховка</option>
                <option value="other">📋 Другое</option>
              </select>
            </div>
          </>
        )}

        {/* Common Fields */}
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
            className="w-full bg-gray-900 text-white px-4 py-3 rounded-lg border border-gray-700 focus:outline-none focus:border-green-500"
            required
          />
        </div>

        <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
          <label className="block text-sm font-semibold text-gray-300 mb-2">
            Дата <span className="text-red-500">*</span>
          </label>
          <input
            type="date"
            name="entry_date"
            value={formData.entry_date}
            onChange={handleChange}
            className="w-full bg-gray-900 text-white px-4 py-3 rounded-lg border border-gray-700 focus:outline-none focus:border-green-500"
            required
          />
        </div>

        {/* Submit */}
        <button
          type="submit"
          disabled={saving}
          className="w-full bg-gradient-to-r from-green-500 to-green-600 text-white py-4 px-6 rounded-xl shadow-lg hover:shadow-xl transition disabled:opacity-50 flex items-center justify-center space-x-3 font-bold"
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

export default AddLog;
