import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Plus, Car, Wrench, Calendar, Bell, FileText, AlertCircle, Trash2 } from 'lucide-react';
import { showAlert } from '../utils/telegram';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Garage = ({ userData, navigateTo }) => {
  const [vehicles, setVehicles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedVehicleId, setSelectedVehicleId] = useState(null);

  useEffect(() => {
    loadVehicles();
  }, []);

  const loadVehicles = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/garage/${userData.telegram_id}`);
      setVehicles(response.data.vehicles || []);
    } catch (error) {
      console.error('Error loading vehicles:', error);
      showAlert('Ошибка загрузки автомобилей');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteVehicle = async (vehicleId, e) => {
    e.stopPropagation(); // Предотвращаем переход на детальную страницу
    
    if (!window.confirm('Удалить этот автомобиль? Все данные об обслуживании, записи и напоминания будут удалены.')) {
      return;
    }
    
    try {
      console.log('Deleting vehicle:', vehicleId);
      await axios.delete(`${API}/garage/vehicle/${vehicleId}`);
      showAlert('✅ Автомобиль удален');
      loadVehicles(); // Перезагружаем список
    } catch (error) {
      console.error('Error deleting vehicle:', error);
      showAlert('❌ Ошибка при удалении');
    }
  };

  const getVehicleIcon = (make) => {
    // Можно добавить разные иконки для разных марок
    return '🚗';
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-900 via-gray-800 to-gray-900 text-white pb-20">
      {/* Garage Header with toolbox background */}
      <div className="relative bg-gradient-to-r from-gray-900 to-gray-800 p-6 shadow-2xl border-b-4 border-yellow-500">
        <div className="absolute inset-0 opacity-10">
          <div className="h-full w-full bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGRlZnM+PHBhdHRlcm4gaWQ9ImdyaWQiIHdpZHRoPSI2MCIgaGVpZ2h0PSI2MCIgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSI+PHBhdGggZD0iTSAxMCAwIEwgMCAwIDAgMTAiIGZpbGw9Im5vbmUiIHN0cm9rZT0iI2ZmZiIgc3Ryb2tlLXdpZHRoPSIxIi8+PC9wYXR0ZXJuPjwvZGVmcz48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSJ1cmwoI2dyaWQpIi8+PC9zdmc+')]"></div>
        </div>
        <div className="relative z-10">
          <button
            onClick={() => navigateTo('home')}
            className="flex items-center text-yellow-400 mb-4 hover:text-yellow-300"
          >
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Назад
          </button>
          <h1 className="text-3xl font-bold mb-2 flex items-center">
            <Wrench className="mr-3 text-yellow-500" size={32} />
            Мой Гараж
          </h1>
          <p className="text-gray-300">Управление вашими автомобилями</p>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="p-4">
        <button
          onClick={() => navigateTo('add-vehicle')}
          className="w-full bg-gradient-to-r from-yellow-500 to-orange-500 text-gray-900 font-bold py-4 px-6 rounded-xl shadow-lg hover:shadow-xl transition-all flex items-center justify-center space-x-3 mb-6"
        >
          <Plus size={24} />
          <span className="text-lg">Добавить автомобиль</span>
        </button>

        {/* Vehicles Grid */}
        {loading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-yellow-500 mx-auto mb-4"></div>
            <p className="text-gray-400">Загрузка...</p>
          </div>
        ) : vehicles.length === 0 ? (
          <div className="bg-gray-800 rounded-xl p-8 text-center border-2 border-dashed border-gray-600">
            <Car className="mx-auto mb-4 text-gray-600" size={64} />
            <h3 className="text-xl font-semibold mb-2 text-gray-300">Гараж пуст</h3>
            <p className="text-gray-500 mb-4">Добавьте свой первый автомобиль</p>
            <button
              onClick={() => navigateTo('add-vehicle')}
              className="bg-yellow-500 text-gray-900 font-semibold px-6 py-2 rounded-lg hover:bg-yellow-400 transition"
            >
              Добавить авто
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            {vehicles.map((vehicle) => (
              <div
                key={vehicle.id}
                onClick={() => navigateTo('vehicle-detail', vehicle.id)}
                className="bg-gradient-to-r from-gray-800 to-gray-700 rounded-xl p-6 shadow-lg hover:shadow-2xl transition-all cursor-pointer border-l-4 border-yellow-500"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-4 flex-1">
                    {/* Car Icon */}
                    <div className="bg-gray-900 p-4 rounded-lg">
                      <span className="text-4xl">{getVehicleIcon(vehicle.make)}</span>
                    </div>

                    {/* Vehicle Info */}
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-1">
                        <h3 className="text-xl font-bold text-white">
                          {vehicle.make} {vehicle.model}
                        </h3>
                        {vehicle.is_active && (
                          <span className="bg-green-500 text-white text-xs px-2 py-1 rounded-full">
                            Основное
                          </span>
                        )}
                      </div>
                      <p className="text-gray-400 mb-2">{vehicle.year} год</p>
                      
                      {/* Additional Info */}
                      <div className="flex flex-wrap gap-2 text-sm">
                        {vehicle.license_plate && (
                          <span className="bg-gray-900 text-yellow-400 px-2 py-1 rounded font-mono">
                            {vehicle.license_plate}
                          </span>
                        )}
                        <span className="bg-gray-900 text-gray-300 px-2 py-1 rounded">
                          📏 {vehicle.mileage.toLocaleString('ru-RU')} км
                        </span>
                        {vehicle.color && (
                          <span className="bg-gray-900 text-gray-300 px-2 py-1 rounded">
                            🎨 {vehicle.color}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Arrow */}
                  <div className="text-yellow-500 text-2xl">→</div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Quick Access Menu */}
        {vehicles.length > 0 && (
          <div className="mt-8">
            <h3 className="text-lg font-semibold mb-4 text-gray-300">Быстрый доступ</h3>
            
            {/* Vehicle Selector */}
            <select
              value={selectedVehicleId || ''}
              onChange={(e) => setSelectedVehicleId(e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 text-white rounded-xl p-3 mb-4"
            >
              <option value="">Выберите автомобиль</option>
              {vehicles.map((vehicle) => (
                <option key={vehicle.id} value={vehicle.id}>
                  {vehicle.make} {vehicle.model} ({vehicle.year})
                </option>
              ))}
            </select>

            {selectedVehicleId ? (
              <div className="grid grid-cols-2 gap-4">
                <button
                  onClick={() => navigateTo('diagnostics', selectedVehicleId)}
                  className="bg-gray-800 hover:bg-gray-700 p-4 rounded-xl border border-gray-700 transition-all"
                >
                  <AlertCircle className="mx-auto mb-2 text-red-400" size={32} />
                  <p className="text-sm font-semibold text-gray-300">Диагностика</p>
                  <p className="text-xs text-gray-500 mt-1">OBD-II коды</p>
                </button>

                <button
                  onClick={() => navigateTo('service-log', selectedVehicleId)}
                  className="bg-gray-800 hover:bg-gray-700 p-4 rounded-xl border border-gray-700 transition-all"
                >
                  <Wrench className="mx-auto mb-2 text-blue-400" size={32} />
                  <p className="text-sm font-semibold text-gray-300">Обслуживание</p>
                  <p className="text-xs text-gray-500 mt-1">История ТО</p>
                </button>

                <button
                  onClick={() => navigateTo('board-journal', selectedVehicleId)}
                  className="bg-gray-800 hover:bg-gray-700 p-4 rounded-xl border border-gray-700 transition-all"
                >
                  <FileText className="mx-auto mb-2 text-green-400" size={32} />
                  <p className="text-sm font-semibold text-gray-300">Бортжурнал</p>
                  <p className="text-xs text-gray-500 mt-1">Записи</p>
                </button>

                <button
                  onClick={() => navigateTo('reminders', selectedVehicleId)}
                  className="bg-gray-800 hover:bg-gray-700 p-4 rounded-xl border border-gray-700 transition-all"
                >
                  <Bell className="mx-auto mb-2 text-yellow-400" size={32} />
                  <p className="text-sm font-semibold text-gray-300">Напоминания</p>
                  <p className="text-xs text-gray-500 mt-1">ТО, страховка</p>
                </button>
              </div>
            ) : (
              <div className="bg-gray-800 rounded-xl p-6 text-center border-2 border-dashed border-gray-700">
                <p className="text-gray-400">Выберите автомобиль для быстрого доступа</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default Garage;
