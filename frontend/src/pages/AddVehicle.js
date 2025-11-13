import React, { useState } from 'react';
import axios from 'axios';
import { Car, Save, Loader2 } from 'lucide-react';
import { showAlert } from '../utils/telegram';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AddVehicle = ({ userData, navigateTo }) => {
  const [formData, setFormData] = useState({
    make: '',
    model: '',
    year: new Date().getFullYear(),
    vin: '',
    color: '',
    license_plate: '',
    mileage: 0,
    purchase_date: '',
    is_active: true
  });
  const [saving, setSaving] = useState(false);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!formData.make || !formData.model || !formData.year) {
      showAlert('Заполните обязательные поля: марка, модель и год');
      return;
    }

    setSaving(true);
    try {
      await axios.post(`${API}/garage`, {
        ...formData,
        telegram_id: userData.telegram_id,
        year: parseInt(formData.year),
        mileage: parseInt(formData.mileage || 0)
      });

      showAlert('✅ Автомобиль успешно добавлен!');
      navigateTo('garage');
    } catch (error) {
      console.error('Error adding vehicle:', error);
      showAlert('Ошибка при добавлении автомобиля');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-900 via-gray-800 to-gray-900 text-white pb-20">
      {/* Header */}
      <div className="bg-gradient-to-r from-gray-900 to-gray-800 p-6 shadow-2xl border-b-4 border-yellow-500">
        <h1 className="text-2xl font-bold flex items-center">
          <Car className="mr-3 text-yellow-500" size={28} />
          Добавить автомобиль
        </h1>
        <p className="text-gray-400 mt-1">Заполните информацию о вашем авто</p>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit} className="p-4 space-y-4">
        {/* Make */}
        <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
          <label className="block text-sm font-semibold text-gray-300 mb-2">
            Марка <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            name="make"
            value={formData.make}
            onChange={handleChange}
            placeholder="Toyota, BMW, Lada..."
            className="w-full bg-gray-900 text-white px-4 py-3 rounded-lg border border-gray-700 focus:outline-none focus:border-yellow-500"
            required
          />
        </div>

        {/* Model */}
        <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
          <label className="block text-sm font-semibold text-gray-300 mb-2">
            Модель <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            name="model"
            value={formData.model}
            onChange={handleChange}
            placeholder="Camry, X5, Granta..."
            className="w-full bg-gray-900 text-white px-4 py-3 rounded-lg border border-gray-700 focus:outline-none focus:border-yellow-500"
            required
          />
        </div>

        {/* Year */}
        <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
          <label className="block text-sm font-semibold text-gray-300 mb-2">
            Год выпуска <span className="text-red-500">*</span>
          </label>
          <input
            type="number"
            name="year"
            value={formData.year}
            onChange={handleChange}
            min="1900"
            max={new Date().getFullYear() + 1}
            className="w-full bg-gray-900 text-white px-4 py-3 rounded-lg border border-gray-700 focus:outline-none focus:border-yellow-500"
            required
          />
        </div>

        {/* VIN */}
        <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
          <label className="block text-sm font-semibold text-gray-300 mb-2">
            VIN номер
          </label>
          <input
            type="text"
            name="vin"
            value={formData.vin}
            onChange={handleChange}
            placeholder="17 символов"
            maxLength="17"
            className="w-full bg-gray-900 text-white px-4 py-3 rounded-lg border border-gray-700 focus:outline-none focus:border-yellow-500 font-mono uppercase"
          />
        </div>

        {/* License Plate */}
        <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
          <label className="block text-sm font-semibold text-gray-300 mb-2">
            Гос. номер
          </label>
          <input
            type="text"
            name="license_plate"
            value={formData.license_plate}
            onChange={handleChange}
            placeholder="А123БВ72"
            className="w-full bg-gray-900 text-white px-4 py-3 rounded-lg border border-gray-700 focus:outline-none focus:border-yellow-500 font-mono uppercase"
          />
        </div>

        {/* Color */}
        <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
          <label className="block text-sm font-semibold text-gray-300 mb-2">
            Цвет
          </label>
          <input
            type="text"
            name="color"
            value={formData.color}
            onChange={handleChange}
            placeholder="Черный, Белый, Синий..."
            className="w-full bg-gray-900 text-white px-4 py-3 rounded-lg border border-gray-700 focus:outline-none focus:border-yellow-500"
          />
        </div>

        {/* Mileage */}
        <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
          <label className="block text-sm font-semibold text-gray-300 mb-2">
            Текущий пробег (км)
          </label>
          <input
            type="number"
            name="mileage"
            value={formData.mileage}
            onChange={handleChange}
            min="0"
            placeholder="50000"
            className="w-full bg-gray-900 text-white px-4 py-3 rounded-lg border border-gray-700 focus:outline-none focus:border-yellow-500"
          />
        </div>

        {/* Purchase Date */}
        <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
          <label className="block text-sm font-semibold text-gray-300 mb-2">
            Дата покупки
          </label>
          <input
            type="date"
            name="purchase_date"
            value={formData.purchase_date}
            onChange={handleChange}
            className="w-full bg-gray-900 text-white px-4 py-3 rounded-lg border border-gray-700 focus:outline-none focus:border-yellow-500"
          />
        </div>

        {/* Is Active */}
        <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
          <label className="flex items-center space-x-3 cursor-pointer">
            <input
              type="checkbox"
              name="is_active"
              checked={formData.is_active}
              onChange={handleChange}
              className="w-5 h-5 text-yellow-500 bg-gray-900 border-gray-700 rounded focus:ring-yellow-500"
            />
            <span className="text-gray-300">Сделать основным автомобилем</span>
          </label>
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={saving}
          className="w-full bg-gradient-to-r from-yellow-500 to-orange-500 text-gray-900 font-bold py-4 px-6 rounded-xl shadow-lg hover:shadow-xl transition-all disabled:opacity-50 flex items-center justify-center space-x-3"
        >
          {saving ? (
            <>
              <Loader2 className="animate-spin" size={24} />
              <span>Сохранение...</span>
            </>
          ) : (
            <>
              <Save size={24} />
              <span>Добавить автомобиль</span>
            </>
          )}
        </button>
      </form>
    </div>
  );
};

export default AddVehicle;
