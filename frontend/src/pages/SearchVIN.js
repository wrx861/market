import React, { useState } from 'react';
import axios from 'axios';
import { Car, Loader2, Search, ShoppingCart, Sparkles, ArrowLeft } from 'lucide-react';
import { showAlert } from '../utils/telegram';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const SearchVIN = ({ userData, onAddToCart, navigateTo }) => {
  const [vin, setVin] = useState('');
  const [carInfo, setCarInfo] = useState(null);
  const [partQuery, setPartQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [searchingParts, setSearchingParts] = useState(false);
  const [oemParts, setOemParts] = useState([]);

  const handleSearchOEM = async () => {
    if (!vin.trim()) {
      showAlert('Введите VIN номер');
      return;
    }

    if (vin.trim().length !== 17) {
      showAlert('VIN номер должен содержать 17 символов');
      return;
    }

    if (!partQuery.trim()) {
      showAlert('Введите название запчасти');
      return;
    }

    setSearchingParts(true);

    try {
      const response = await axios.post(`${API}/search/vin_oem`, {
        vin: vin.trim().toUpperCase(),
        part_name: partQuery.trim(),
        telegram_id: userData.telegram_id
      });

      if (response.data.vehicle_info) {
        setCarInfo(response.data.vehicle_info);
      }

      if (response.data.oem_parts && response.data.oem_parts.length > 0) {
        setOemParts(response.data.oem_parts);
      } else {
        showAlert('OEM артикулы не найдены. Попробуйте изменить запрос.');
      }
    } catch (error) {
      console.error('Error searching OEM:', error);
      const errorMsg = error.response?.data?.detail || 'Ошибка при поиске в OEM каталоге';
      showAlert(errorMsg);
    } finally {
      setSearchingParts(false);
    }
  };

  const handleAnalyzeVIN = async () => {
    // Старая функция больше не используется
    showAlert('⏳ Используйте новый поиск через OEM каталог!\n\nВведите VIN и название запчасти.');
    return;
    
    /* Отключенный код
    if (!vin.trim()) {
      showAlert('Введите VIN номер');
      return;
    }

    if (vin.trim().length !== 17) {
      showAlert('VIN номер должен содержать 17 символов');
      return;
    }

    setLoading(true);

    try {
      const response = await axios.post(`${API}/search/vin`, {
        vin: vin.trim().toUpperCase(),
        telegram_id: userData.telegram_id
      });

      if (response.data.car_info) {
        setCarInfo(response.data.car_info);
      } else {
        showAlert('Не удалось определить автомобиль по VIN');
      }
    } catch (error) {
      console.error('Error analyzing VIN:', error);
      showAlert('Ошибка при анализе VIN');
    } finally {
      setLoading(false);
    }
    */
  };

  const handlePriceCheck = (article) => {
    // Переход на страницу поиска по артикулу
    navigateTo('search', { article: article });
  };

  const handleAddToCart = (part) => {
    const item = {
      article: part.article,
      name: part.name,
      brand: part.brand,
      price: part.price,
      quantity: 1,
      delivery_days: part.delivery_days,
      supplier: part.supplier
    };

    onAddToCart(item);
  };

  return (
    <div className="min-h-screen bg-gray-50 pb-20">
      {/* Header */}
      <div className="bg-gradient-to-r from-green-600 to-green-700 text-white p-6">
        <button
          onClick={() => navigateTo('home')}
          className="flex items-center text-white mb-4 hover:text-green-100"
        >
          <ArrowLeft size={20} className="mr-2" />
          Назад
        </button>
        <h1 className="text-2xl font-bold mb-2 flex items-center">
          <Car className="mr-2" />
          Поиск по VIN
        </h1>
        <p className="text-sm text-green-100">Используем AI для поиска</p>
      </div>

      <div className="p-4">
        {/* VIN & Part Search Form */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            VIN номер
          </label>
          <input
            type="text"
            value={vin}
            onChange={(e) => setVin(e.target.value.toUpperCase())}
            maxLength={17}
            placeholder="Введите 17-значный VIN"
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent font-mono mb-1"
            data-testid="vin-input"
          />
          <p className="text-xs text-gray-500 mb-4">
            Введено: {vin.length}/17 символов
          </p>

          <label className="block text-sm font-medium text-gray-700 mb-2">
            Название запчасти
          </label>
          <input
            type="text"
            value={partQuery}
            onChange={(e) => setPartQuery(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearchOEM()}
            placeholder="Например: шаровая опора, рулевая рейка..."
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
            data-testid="part-query-input"
          />

          <button
            onClick={handleSearchOEM}
            disabled={searchingParts || vin.length !== 17 || !partQuery.trim()}
            className="w-full mt-4 bg-gradient-to-r from-green-600 to-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:opacity-90 transition disabled:opacity-50 flex items-center justify-center"
            data-testid="search-oem-button"
          >
            {searchingParts ? (
              <>
                <Loader2 className="animate-spin mr-2" size={20} />
                Ищем в OEM каталоге...
              </>
            ) : (
              <>
                <Search className="mr-2" size={20} />
                Найти OEM артикулы
              </>
            )}
          </button>
        </div>

        {/* Vehicle Info */}
        {carInfo && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-4">
            <h2 className="text-xl font-bold text-gray-800 mb-4 flex items-center">
              <Car className="mr-2 text-green-600" />
              Информация об автомобиле
            </h2>
            <div className="space-y-2 text-sm text-gray-700">
              <p><span className="font-semibold">Бренд:</span> {carInfo.brand || 'N/A'}</p>
              <p><span className="font-semibold">Название:</span> {carInfo.name || 'N/A'}</p>
              <p><span className="font-semibold">Модель:</span> {carInfo.model || 'N/A'}</p>
              
              {carInfo.release_date && (
                <p><span className="font-semibold">Дата выпуска:</span> {carInfo.release_date}</p>
              )}
              
              {carInfo.engine && (
                <p><span className="font-semibold">Двигатель:</span> {carInfo.engine}</p>
              )}
              
              {carInfo.transmission && (
                <p><span className="font-semibold">КПП:</span> {carInfo.transmission}</p>
              )}
            </div>
          </div>
        )}

        {/* OEM Parts Results */}
        {oemParts.length > 0 && (
          <div className="space-y-3">
            <h2 className="text-lg font-semibold text-gray-800 bg-white rounded-lg shadow-md p-4">
              🔧 Найдено OEM артикулов: {oemParts.length}
            </h2>
            {oemParts.map((part, index) => (
              <div
                key={index}
                className="bg-white rounded-lg shadow-md p-4 hover:shadow-lg transition"
                data-testid={`oem-part-${index}`}
              >
                <div className="flex justify-between items-start mb-3">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="bg-green-100 text-green-800 text-xs font-semibold px-2 py-1 rounded">
                        OEM
                      </span>
                      <span className="font-mono text-lg font-bold text-gray-800">
                        {part.article}
                      </span>
                    </div>
                    <h3 className="text-gray-700 font-medium">{part.name}</h3>
                    <p className="text-xs text-gray-500 mt-1">{part.source}</p>
                  </div>
                </div>

                <button
                  onClick={() => handlePriceCheck(part.article)}
                  className="w-full bg-gradient-to-r from-blue-600 to-green-600 text-white px-4 py-3 rounded-lg hover:opacity-90 transition flex items-center justify-center gap-2 font-semibold"
                  data-testid={`price-check-${index}`}
                >
                  <Search size={18} />
                  <span>Проценка</span>
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default SearchVIN;
