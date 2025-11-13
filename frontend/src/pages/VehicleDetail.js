import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { ArrowLeft, Edit, Trash2, Wrench, FileText, Bell, TrendingUp, Calendar, DollarSign } from 'lucide-react';
import { showAlert, showConfirm } from '../utils/telegram';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const VehicleDetail = ({ userData, navigateTo, vehicleId }) => {
  const [vehicle, setVehicle] = useState(null);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadVehicleDetail();
  }, [vehicleId]);

  const loadVehicleDetail = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/garage/vehicle/${vehicleId}`);
      setVehicle(response.data.vehicle);
      setStats(response.data.stats);
    } catch (error) {
      console.error('Error loading vehicle:', error);
      showAlert('Ошибка загрузки автомобиля');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = () => {
    showConfirm(
      'Вы уверены, что хотите удалить этот автомобиль?\n\nВсе данные будут удалены:\n• История обслуживания\n• Записи бортжурнала\n• Напоминания\n• Диагностика\n• Расходы',
      async (confirmed) => {
        if (!confirmed) {
          console.log('Deletion cancelled by user');
          return;
        }
        
        try {
          console.log('User confirmed deletion. Deleting vehicle:', vehicleId);
          showAlert('⏳ Удаление автомобиля...');
          
          const response = await axios.delete(`${API}/garage/vehicle/${vehicleId}`);
          console.log('Delete response:', response.data);
          
          showAlert('✅ Автомобиль успешно удален!', () => {
            console.log('Navigating to garage');
            navigateTo('garage');
          });
        } catch (error) {
          console.error('Error deleting vehicle:', error);
          console.error('Error details:', error.response?.data);
          showAlert('❌ Ошибка при удалении автомобиля. Попробуйте еще раз.');
        }
      }
    );
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-gray-900 via-gray-800 to-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-yellow-500 mx-auto mb-4"></div>
          <p className="text-gray-400">Загрузка...</p>
        </div>
      </div>
    );
  }

  if (!vehicle) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-gray-900 via-gray-800 to-gray-900 flex items-center justify-center">
        <div className="text-center text-white">
          <p className="text-xl mb-4">Автомобиль не найден</p>
          <button
            onClick={() => navigateTo('garage')}
            className="bg-yellow-500 text-gray-900 px-6 py-2 rounded-lg"
          >
            Вернуться в гараж
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-900 via-gray-800 to-gray-900 text-white pb-20">
      {/* Header */}
      <div className="bg-gradient-to-r from-gray-900 to-gray-800 p-6 shadow-2xl border-b-4 border-yellow-500">
        <button
          onClick={() => navigateTo('garage')}
          className="flex items-center text-yellow-500 mb-4 hover:text-yellow-400"
        >
          <ArrowLeft size={20} className="mr-2" />
          Назад в гараж
        </button>
        
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold mb-2">
              {vehicle.make} {vehicle.model}
            </h1>
            <p className="text-gray-400">{vehicle.year} год</p>
          </div>
          
          {vehicle.is_active && (
            <span className="bg-green-500 text-white px-3 py-1 rounded-full text-sm">
              Основное
            </span>
          )}
        </div>
      </div>

      <div className="p-4 space-y-4">
        {/* Main Info Card */}
        <div className="bg-gradient-to-r from-gray-800 to-gray-700 rounded-xl p-6 border-l-4 border-yellow-500 shadow-lg">
          <div className="grid grid-cols-2 gap-4 text-sm">
            {vehicle.license_plate && (
              <div>
                <p className="text-gray-400 mb-1">Гос. номер</p>
                <p className="font-mono font-bold text-yellow-400 text-lg">{vehicle.license_plate}</p>
              </div>
            )}
            
            <div>
              <p className="text-gray-400 mb-1">Пробег</p>
              <p className="font-bold text-lg">{vehicle.mileage.toLocaleString('ru-RU')} км</p>
            </div>
            
            {vehicle.color && (
              <div>
                <p className="text-gray-400 mb-1">Цвет</p>
                <p className="font-semibold">{vehicle.color}</p>
              </div>
            )}
            
            {vehicle.vin && (
              <div>
                <p className="text-gray-400 mb-1">VIN</p>
                <p className="font-mono text-xs">{vehicle.vin}</p>
              </div>
            )}
          </div>
        </div>

        {/* Statistics */}
        {stats && (
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
              <Wrench className="text-blue-400 mb-2" size={24} />
              <p className="text-2xl font-bold">{stats.service_count}</p>
              <p className="text-sm text-gray-400">Обслуживаний</p>
            </div>
            
            <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
              <FileText className="text-green-400 mb-2" size={24} />
              <p className="text-2xl font-bold">{stats.log_count}</p>
              <p className="text-sm text-gray-400">Записей</p>
            </div>
            
            <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
              <Bell className="text-yellow-400 mb-2" size={24} />
              <p className="text-2xl font-bold">{stats.active_reminders}</p>
              <p className="text-sm text-gray-400">Напоминаний</p>
            </div>
            
            <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
              <Calendar className="text-purple-400 mb-2" size={24} />
              <p className="text-sm text-gray-400">Последнее ТО</p>
              <p className="text-xs font-semibold">
                {stats.last_service 
                  ? new Date(stats.last_service.service_date).toLocaleDateString('ru-RU')
                  : 'Нет данных'
                }
              </p>
            </div>
          </div>
        )}

        {/* Quick Actions */}
        <div className="space-y-3 mt-6">
          <button
            onClick={() => navigateTo('add-service', vehicleId)}
            className="w-full bg-gradient-to-r from-blue-600 to-blue-700 text-white py-4 px-6 rounded-xl flex items-center justify-center space-x-3 shadow-lg hover:shadow-xl transition"
          >
            <Wrench size={24} />
            <span className="font-semibold">Добавить обслуживание</span>
          </button>
          
          <button
            onClick={() => navigateTo('add-log', vehicleId)}
            className="w-full bg-gradient-to-r from-green-600 to-green-700 text-white py-4 px-6 rounded-xl flex items-center justify-center space-x-3 shadow-lg hover:shadow-xl transition"
          >
            <FileText size={24} />
            <span className="font-semibold">Добавить запись</span>
          </button>
          
          <button
            onClick={() => navigateTo('add-reminder', vehicleId)}
            className="w-full bg-gradient-to-r from-yellow-600 to-orange-600 text-white py-4 px-6 rounded-xl flex items-center justify-center space-x-3 shadow-lg hover:shadow-xl transition"
          >
            <Bell size={24} />
            <span className="font-semibold">Создать напоминание</span>
          </button>
        </div>

        {/* View History */}
        <div className="grid grid-cols-3 gap-3 mt-4">
          <button
            onClick={() => navigateTo('service-log', vehicleId)}
            className="bg-gray-800 hover:bg-gray-700 p-4 rounded-xl border border-gray-700 transition"
          >
            <Wrench className="mx-auto mb-2 text-blue-400" size={28} />
            <p className="text-sm font-semibold">История ТО</p>
          </button>
          
          <button
            onClick={() => navigateTo('board-journal', vehicleId)}
            className="bg-gray-800 hover:bg-gray-700 p-4 rounded-xl border border-gray-700 transition"
          >
            <FileText className="mx-auto mb-2 text-green-400" size={28} />
            <p className="text-sm font-semibold">Бортжурнал</p>
          </button>
          
          <button
            onClick={() => navigateTo('expenses', vehicleId)}
            className="bg-gray-800 hover:bg-gray-700 p-4 rounded-xl border border-gray-700 transition"
          >
            <DollarSign className="mx-auto mb-2 text-purple-400" size={28} />
            <p className="text-sm font-semibold">Расходы</p>
          </button>
        </div>

        {/* Danger Zone */}
        <div className="mt-8 bg-red-900 bg-opacity-20 border border-red-500 rounded-xl p-4">
          <h3 className="text-red-400 font-semibold mb-3 flex items-center">
            <Trash2 size={20} className="mr-2" />
            Опасная зона
          </h3>
          <button
            onClick={handleDelete}
            className="w-full bg-red-600 hover:bg-red-700 text-white py-3 px-4 rounded-lg font-semibold transition"
          >
            Удалить автомобиль
          </button>
        </div>
      </div>
    </div>
  );
};

export default VehicleDetail;
