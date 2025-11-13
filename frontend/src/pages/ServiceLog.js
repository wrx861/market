import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { ArrowLeft, Wrench, Plus, Calendar, DollarSign, TrendingUp } from 'lucide-react';
import { showAlert } from '../utils/telegram';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const ServiceLog = ({ userData, navigateTo, vehicleId }) => {
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [totalCost, setTotalCost] = useState(0);

  useEffect(() => {
    loadServiceRecords();
  }, [vehicleId]);

  const loadServiceRecords = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/garage/vehicle/${vehicleId}/service`);
      const data = response.data.records || [];
      setRecords(data);
      
      const total = data.reduce((sum, record) => sum + (record.cost || 0), 0);
      setTotalCost(total);
    } catch (error) {
      console.error('Error loading service records:', error);
      showAlert('Ошибка загрузки истории обслуживания');
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = (record) => {
    navigateTo('add-service', vehicleId, record);
  };

  const handleDelete = async (recordId) => {
    if (!window.confirm('Удалить эту запись?')) return;
    
    try {
      await axios.delete(`${API}/garage/service/${recordId}`);
      showAlert('✅ Запись удалена');
      loadServiceRecords();
    } catch (error) {
      console.error('Error deleting record:', error);
      showAlert('Ошибка удаления');
    }
  };

  const getServiceTypeLabel = (type) => {
    const labels = {
      'oil_change': '🛢️ Замена масла',
      'tire_change': '🛞 Замена шин',
      'brake_service': '🔴 Обслуживание тормозов',
      'general_maintenance': '🔧 Общее ТО',
      'repair': '⚙️ Ремонт',
      'other': '📋 Другое'
    };
    return labels[type] || type;
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-900 via-gray-800 to-gray-900 text-white pb-20">
      <div className="bg-gradient-to-r from-gray-900 to-gray-800 p-6 shadow-2xl border-b-4 border-blue-500">
        <button
          onClick={() => navigateTo('vehicle-detail', vehicleId)}
          className="flex items-center text-blue-400 mb-4 hover:text-blue-300"
        >
          <ArrowLeft size={20} className="mr-2" />
          Назад
        </button>
        
        <h1 className="text-2xl font-bold flex items-center">
          <Wrench className="mr-3 text-blue-400" size={28} />
          История обслуживания
        </h1>
      </div>

      <div className="p-4">
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div className="bg-gradient-to-r from-blue-600 to-blue-700 rounded-xl p-4 shadow-lg">
            <TrendingUp className="mb-2 text-white" size={24} />
            <p className="text-2xl font-bold text-white">{records.length}</p>
            <p className="text-sm text-blue-100">Всего записей</p>
          </div>
          
          <div className="bg-gradient-to-r from-green-600 to-green-700 rounded-xl p-4 shadow-lg">
            <DollarSign className="mb-2 text-white" size={24} />
            <p className="text-2xl font-bold text-white">{totalCost.toLocaleString('ru-RU')} ₽</p>
            <p className="text-sm text-green-100">Потрачено</p>
          </div>
        </div>

        <button
          onClick={() => navigateTo('add-service', vehicleId)}
          className="w-full bg-gradient-to-r from-blue-500 to-blue-600 text-white py-4 px-6 rounded-xl flex items-center justify-center space-x-3 shadow-lg hover:shadow-xl transition mb-6"
        >
          <Plus size={24} />
          <span className="font-semibold">Добавить обслуживание</span>
        </button>

        {loading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
            <p className="text-gray-400">Загрузка...</p>
          </div>
        ) : records.length === 0 ? (
          <div className="bg-gray-800 rounded-xl p-8 text-center border-2 border-dashed border-gray-600">
            <Wrench className="mx-auto mb-4 text-gray-600" size={64} />
            <h3 className="text-xl font-semibold mb-2 text-gray-300">История пуста</h3>
            <p className="text-gray-500 mb-4">Добавьте первую запись об обслуживании</p>
          </div>
        ) : (
          <div className="space-y-3">
            {records.map((record, index) => (
              <div
                key={record.id || index}
                className="bg-gradient-to-r from-gray-800 to-gray-700 rounded-xl p-5 shadow-lg border-l-4 border-blue-500"
              >
                <div className="flex justify-between items-start mb-3">
                  <div className="flex-1">
                    <p className="text-lg font-semibold mb-1">
                      {getServiceTypeLabel(record.service_type)}
                    </p>
                    <p className="text-gray-400 text-sm">{record.title}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="bg-blue-500 text-white px-3 py-1 rounded-full text-sm font-bold">
                      {record.cost ? `${record.cost.toLocaleString('ru-RU')} ₽` : 'Бесплатно'}
                    </span>
                    <div className="action-buttons">
                      <button onClick={() => handleEdit(record)} className="action-btn edit-btn" title="Редактировать">✏️</button>
                      <button onClick={() => handleDelete(record.id)} className="action-btn delete-btn" title="Удалить">🗑️</button>
                    </div>
                  </div>
                </div>

                {record.description && (
                  <p className="text-gray-400 text-sm mb-3 border-l-2 border-gray-600 pl-3">
                    {record.description}
                  </p>
                )}

                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div className="bg-gray-900 rounded-lg p-2">
                    <p className="text-gray-500 text-xs">Дата</p>
                    <p className="font-semibold">
                      {new Date(record.service_date).toLocaleDateString('ru-RU')}
                    </p>
                  </div>
                  
                  <div className="bg-gray-900 rounded-lg p-2">
                    <p className="text-gray-500 text-xs">Пробег</p>
                    <p className="font-semibold">{record.mileage.toLocaleString('ru-RU')} км</p>
                  </div>
                </div>

                {record.service_provider && (
                  <div className="mt-2 bg-gray-900 rounded-lg p-2">
                    <p className="text-gray-500 text-xs">Исполнитель</p>
                    <p className="font-semibold text-sm">{record.service_provider}</p>
                  </div>
                )}

                {record.parts_used && record.parts_used.length > 0 && (
                  <div className="mt-2">
                    <p className="text-gray-400 text-xs mb-1">Использованные запчасти:</p>
                    <div className="flex flex-wrap gap-1">
                      {record.parts_used.map((part, i) => (
                        <span key={i} className="bg-gray-900 text-blue-300 px-2 py-1 rounded text-xs">
                          {part}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ServiceLog;
