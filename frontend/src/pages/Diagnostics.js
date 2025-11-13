import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { ArrowLeft, AlertCircle, Search, Loader2, Brain } from 'lucide-react';
import { showAlert } from '../utils/telegram';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Diagnostics = ({ userData, navigateTo }) => {
  const [vehicles, setVehicles] = useState([]);
  const [selectedVehicle, setSelectedVehicle] = useState('');
  const [obdCode, setObdCode] = useState('');
  const [diagnosing, setDiagnosing] = useState(false);
  const [diagnosis, setDiagnosis] = useState(null);

  useEffect(() => {
    loadVehicles();
  }, []);

  const loadVehicles = async () => {
    try {
      const response = await axios.get(`${API}/garage/${userData.telegram_id}`);
      const vehiclesList = response.data.vehicles || [];
      setVehicles(vehiclesList);
      
      // Выбираем активный автомобиль по умолчанию
      const activeVehicle = vehiclesList.find(v => v.is_active);
      if (activeVehicle) {
        setSelectedVehicle(activeVehicle.id);
      } else if (vehiclesList.length > 0) {
        setSelectedVehicle(vehiclesList[0].id);
      }
    } catch (error) {
      console.error('Error loading vehicles:', error);
    }
  };

  const handleDiagnose = async () => {
    if (!selectedVehicle) {
      showAlert('Выберите автомобиль');
      return;
    }

    if (!obdCode.trim()) {
      showAlert('Введите код ошибки');
      return;
    }

    setDiagnosing(true);
    setDiagnosis(null);

    try {
      const response = await axios.post(`${API}/garage/diagnostics`, {
        obd_code: obdCode.toUpperCase().trim(),
        vehicle_id: selectedVehicle,
        telegram_id: userData.telegram_id
      });

      setDiagnosis({
        code: response.data.obd_code,
        vehicle: response.data.vehicle,
        result: response.data.diagnosis
      });
    } catch (error) {
      console.error('Error diagnosing:', error);
      showAlert('Ошибка при диагностике');
    } finally {
      setDiagnosing(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-900 via-gray-800 to-gray-900 text-white pb-20">
      {/* Header */}
      <div className="bg-gradient-to-r from-red-900 to-red-800 p-6 shadow-2xl border-b-4 border-red-500">
        <button
          onClick={() => navigateTo('garage')}
          className="flex items-center text-red-300 mb-4 hover:text-red-200"
        >
          <ArrowLeft size={20} className="mr-2" />
          Назад в гараж
        </button>
        
        <h1 className="text-2xl font-bold flex items-center">
          <AlertCircle className="mr-3 text-red-400" size={28} />
          Диагностика OBD-II
        </h1>
        <p className="text-red-200 text-sm mt-2">
          Расшифровка кодов ошибок через AI
        </p>
      </div>

      <div className="p-4 space-y-4">
        {/* Info Card */}
        <div className="bg-blue-900 bg-opacity-30 border border-blue-500 rounded-xl p-4">
          <div className="flex items-start space-x-3">
            <Brain className="text-blue-400 flex-shrink-0 mt-1" size={24} />
            <div>
              <p className="font-semibold text-blue-300 mb-1">AI-диагностика</p>
              <p className="text-sm text-gray-300">
                Введите код ошибки (например P0300, P0420) и получите детальную расшифровку
                с рекомендациями по устранению от искусственного интеллекта.
              </p>
            </div>
          </div>
        </div>

        {/* Vehicle Selection */}
        {vehicles.length > 0 && (
          <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
            <label className="block text-sm font-semibold text-gray-300 mb-2">
              Выберите автомобиль
            </label>
            <select
              value={selectedVehicle}
              onChange={(e) => setSelectedVehicle(e.target.value)}
              className="w-full bg-gray-900 text-white px-4 py-3 rounded-lg border border-gray-700 focus:outline-none focus:border-red-500"
            >
              {vehicles.map((vehicle) => (
                <option key={vehicle.id} value={vehicle.id}>
                  {vehicle.make} {vehicle.model} ({vehicle.year})
                </option>
              ))}
            </select>
          </div>
        )}

        {/* OBD Code Input */}
        <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
          <label className="block text-sm font-semibold text-gray-300 mb-2">
            Код ошибки OBD-II
          </label>
          <div className="flex space-x-2">
            <input
              type="text"
              value={obdCode}
              onChange={(e) => setObdCode(e.target.value.toUpperCase())}
              onKeyPress={(e) => e.key === 'Enter' && handleDiagnose()}
              placeholder="P0300, P0420, C0035..."
              className="flex-1 bg-gray-900 text-white px-4 py-3 rounded-lg border border-gray-700 focus:outline-none focus:border-red-500 font-mono uppercase"
              maxLength="10"
            />
            <button
              onClick={handleDiagnose}
              disabled={diagnosing || !selectedVehicle || !obdCode}
              className="bg-gradient-to-r from-red-500 to-red-600 text-white px-6 py-3 rounded-lg font-semibold hover:from-red-600 hover:to-red-700 transition disabled:opacity-50 flex items-center space-x-2"
            >
              {diagnosing ? (
                <>
                  <Loader2 className="animate-spin" size={20} />
                  <span>Анализ...</span>
                </>
              ) : (
                <>
                  <Search size={20} />
                  <span>Диагностика</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Common Codes */}
        <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
          <p className="text-sm font-semibold text-gray-300 mb-3">Частые коды ошибок:</p>
          <div className="flex flex-wrap gap-2">
            {['P0300', 'P0420', 'P0171', 'P0128', 'P0456', 'C0035'].map((code) => (
              <button
                key={code}
                onClick={() => setObdCode(code)}
                className="bg-gray-900 hover:bg-gray-700 text-gray-300 px-3 py-2 rounded-lg text-sm font-mono transition"
              >
                {code}
              </button>
            ))}
          </div>
        </div>

        {/* Diagnosis Result */}
        {diagnosis && (
          <div className="bg-gradient-to-r from-gray-800 to-gray-700 rounded-xl p-6 shadow-2xl border-l-4 border-red-500">
            <div className="flex items-center space-x-3 mb-4">
              <div className="bg-red-500 p-3 rounded-lg">
                <AlertCircle size={24} className="text-white" />
              </div>
              <div>
                <p className="text-xs text-gray-400">Диагностика завершена</p>
                <p className="text-xl font-bold">{diagnosis.code}</p>
                <p className="text-sm text-gray-400">{diagnosis.vehicle}</p>
              </div>
            </div>

            <div className="bg-gray-900 rounded-lg p-4 whitespace-pre-wrap text-sm leading-relaxed">
              {diagnosis.result}
            </div>

            <div className="mt-4 bg-green-900 bg-opacity-30 border border-green-500 rounded-lg p-3">
              <p className="text-xs text-green-300 flex items-center">
                <AlertCircle size={14} className="mr-2" />
                Диагностика сохранена в бортжурнал
              </p>
            </div>
          </div>
        )}

        {/* No Vehicles Warning */}
        {vehicles.length === 0 && (
          <div className="bg-yellow-900 bg-opacity-30 border border-yellow-500 rounded-xl p-4">
            <p className="text-yellow-300 text-sm">
              ⚠️ Добавьте автомобиль в гараж для использования диагностики
            </p>
            <button
              onClick={() => navigateTo('add-vehicle')}
              className="mt-3 bg-yellow-500 text-gray-900 px-4 py-2 rounded-lg font-semibold hover:bg-yellow-400 transition"
            >
              Добавить автомобиль
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default Diagnostics;
